from xml.dom import minidom

from diplomacy.engine.renderer import Renderer, _attr, ARMY
from diplomacy.utils.equilateral_triangle import EquilateralTriangle
from utils import OrderEnum


class CustomRenderer(Renderer):

    def __init__(self, game, svg_path=None, phase=None):
        super().__init__(game, svg_path)
        self.phase = phase
        self.background = None
        self.background_inserted = False

        self.opacities = {
            "austria": 0.5,
            "england": 0.25,
            "france": 0.25,
            "germany": 0.25,
            "italy": 0.25,
            "russia": 0.25,
            "turkey": 0.25
        }

        self.order_dict = {
            OrderEnum.NO_ORDER: None,
            OrderEnum.HOLD_ORDER: self._issue_hold_order,
            OrderEnum.MOVE_ORDER: self._issue_move_order,
            OrderEnum.SUPPORT_MOVE_ORDER: self._issue_support_move_order,
            OrderEnum.SUPPORT_HOLD_ORDER: self._issue_support_hold_order,
            OrderEnum.CONVOY_ORDER: self._issue_convoy_order
        }

        self.custom_order_dict = {
            OrderEnum.NO_ORDER: None,
            OrderEnum.HOLD_ORDER: self.custom_issue_hold_order,
            OrderEnum.MOVE_ORDER: self.custom_issue_move_order,
            OrderEnum.SUPPORT_MOVE_ORDER: self.custom_issue_support_move_order,
            OrderEnum.SUPPORT_HOLD_ORDER: self.custom_issue_support_hold_order,
            OrderEnum.CONVOY_ORDER: self.custom_issue_convoy_order
        }

    def apply_weight_opacity(g_node, weight):
        g_node.setAttribute('opacity', str(weight))

    def scale_weight(weight):
        return 1.2 - (1 - weight) * 3 / 4

    # Adapted from the renderer method of the Renderer class
    def custom_render(self, incl_orders=True, incl_abbrev=False, output_format='svg', output_path=None, alterations=None):
        self.background_inserted = False
        if output_format not in ['svg']:
            raise ValueError('Only "svg" format is current supported.')
        if not self.game or not self.game.map or not self.xml_map:
            return None

        # Parsing XML
        xml_map = minidom.parseString(self.xml_map)

        # Resetting transparencies for opacity rendering
        style_elements = xml_map.getElementsByTagName('style')
        for style in style_elements:
            style_contents = style.firstChild.nodeValue
            if '.shadowdash' in style_contents:
                new_contents = style_contents.replace('opacity:0.45', '').strip()
                style.firstChild.nodeValue = new_contents
        altered_symbols = ["ConvoyTriangle", "SupportHoldUnit"]
        for symbol in altered_symbols:
            symbol_element = None
            for element in xml_map.getElementsByTagName('*'):
                if element.getAttribute('id') == symbol:
                    symbol_element = element
            if not symbol_element:
                continue
            polygon_elements = symbol_element.getElementsByTagName('polygon')
            for polygon in polygon_elements:
                if polygon.hasAttribute('opacity'):
                    polygon.removeAttribute('opacity')

        # Setting phase and note
        nb_centers = [(power.name[:3], len(power.centers))
                      for power in self.game.powers.values()
                      if not power.is_eliminated()]
        nb_centers = sorted(nb_centers, key=lambda key: key[1], reverse=True)
        nb_centers_per_power = ' '.join(['{}: {}'.format(name, centers) for name, centers in nb_centers])
        if self.phase:
            xml_map = self._set_current_phase(xml_map, self.phase)
        else:
            xml_map = self._set_current_phase(xml_map, self.game.get_current_phase())
        xml_map = self._set_note(xml_map, nb_centers_per_power, self.game.note)

        self.background = xml_map.createElement('g')
        self.background.setAttribute('id', 'back')

        # Adding units and influence
        for i, power in enumerate(self.game.powers.values()):
            for unit in power.units:
                xml_map = self._add_unit(xml_map, unit, power.name, is_dislodged=False)
            for unit in power.retreats:
                xml_map = self._add_unit(xml_map, unit, power.name, is_dislodged=True)
            for center in power.centers:
                xml_map = self.custom_set_influence(xml_map, center, power.name, has_supply_center=True)
            for loc in power.influence:
                xml_map = self.custom_set_influence(xml_map, loc, power.name, has_supply_center=False)

            # Orders
            if incl_orders:

                # Regular orders (Normalized)
                # A PAR H
                # A PAR - BUR [VIA]
                # A PAR S BUR
                # A PAR S F BRE - PIC
                # F BRE C A PAR - LON
                for order_key in power.orders:

                    if order_key[0] in 'RIO':
                        order = power.orders[order_key]
                    else:
                        order = '{} {}'.format(order_key, power.orders[order_key])
                    order_type, order_args = self.parse_order(order, power)
                    xml_map = self.display_order(order_type, order_args, xml_map)

                # Adjustment orders
                # VOID xxx
                # A PAR B
                # A PAR D
                # A PAR R BUR
                # WAIVE
                for order in power.adjust:
                    tokens = order.split()
                    if not tokens or tokens[0] == 'VOID' or tokens[-1] == 'WAIVE':
                        continue
                    elif tokens[-1] == 'B':
                        if len(tokens) < 3:
                            continue
                        xml_map = self._issue_build_order(xml_map, tokens[0], tokens[1], power.name)
                    elif tokens[-1] == 'D':
                        xml_map = self._issue_disband_order(xml_map, tokens[1])
                    elif tokens[-2] == 'R':
                        src_loc = tokens[1] if tokens[0] == 'A' or tokens[0] == 'F' else tokens[0]
                        dest_loc = tokens[-1]
                        xml_map = self._issue_move_order(xml_map, src_loc, dest_loc, power.name)
                    else:
                        raise RuntimeError('Unknown order: {}'.format(order))

            # Alterations
            if alterations:
                for order, weight in alterations[i]:
                    order = order.replace('\\', '')
                    order_type, order_args = self.parse_order(order, power)
                    xml_map = self.custom_display_order(order_type, order_args, xml_map, weight)

        # Removing abbrev and mouse layer
        svg_node = xml_map.getElementsByTagName('svg')[0]
        for child_node in svg_node.childNodes:
            if child_node.nodeName != 'g':
                continue
            if _attr(child_node, 'id') == 'BriefLabelLayer' and not incl_abbrev:
                svg_node.removeChild(child_node)
            elif _attr(child_node, 'id') == 'MouseLayer':
                svg_node.removeChild(child_node)

        # Rendering
        rendered_image = xml_map.toxml()

        # Saving to disk
        if output_path:
            with open(output_path, 'w') as output_file:
                output_file.write(rendered_image)

        # Returning
        return rendered_image

    def display_order(self, order_type, order_args, xml_map):
        if order_type is None:
            return xml_map
        else:
            return self.order_dict[order_type](xml_map, *order_args)

    def custom_display_order(self, order_type, order_args, xml_map, weight=1):
        if order_type is None:
            return xml_map
        else:
            return self.custom_order_dict[order_type](xml_map, *order_args, weight)

    def parse_order(self, order, power):

        # Normalizing and splitting in tokens
        tokens = self._norm_order(order)
        unit_loc = tokens[1]

        # Parsing based on order type
        if not tokens or len(tokens) < 3:
            return None, None

        elif tokens[2] == 'H':
            return OrderEnum.HOLD_ORDER, [unit_loc, power.name]

        elif tokens[2] == '-':
            dest_loc = tokens[-1] if tokens[-1] != 'VIA' else tokens[-2]
            return OrderEnum.MOVE_ORDER, [unit_loc, dest_loc, power.name]

        elif tokens[2] == 'S':
            dest_loc = tokens[-1]
            if '-' in tokens:
                src_loc = tokens[4] if tokens[3] == 'A' or tokens[3] == 'F' else tokens[3]
                return OrderEnum.SUPPORT_MOVE_ORDER, [unit_loc, src_loc, dest_loc, power.name]
            else:
                return OrderEnum.SUPPORT_HOLD_ORDER, [unit_loc, dest_loc, power.name]

        elif tokens[2] == 'C':
            src_loc = tokens[4] if tokens[3] == 'A' or tokens[3] == 'F' else tokens[3]
            dest_loc = tokens[-1]
            if src_loc != dest_loc and '-' in tokens:
                return OrderEnum.CONVOY_ORDER, [unit_loc, src_loc, dest_loc, power.name]
        else:
            raise RuntimeError('Unknown order: {}'.format(' '.join(tokens)))

    def custom_set_influence(self, xml_map, loc, power_name, has_supply_center=False):
        """ Sets the influence on the map

            :param xml_map: The xml map being generated
            :param loc: The province being influenced (e.g. 'PAR')
            :param power_name: The name of the power influencing the province
            :param has_supply_center: Boolean flag to acknowledge we are modifying a loc with a SC
            :return: Nothing
        """
        loc = loc.upper()[:3]
        if loc in self.game.map.scs and not has_supply_center:
            return xml_map
        if self.game.map.area_type(loc) == 'WATER':
            return xml_map

        class_name = power_name.lower() if power_name else 'nopower'

        # Inserting
        map_layer = None
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'MapLayer':
                map_layer = child_node
                break

        if map_layer:
            if not self.background_inserted:
                first_path = map_layer.getElementsByTagName('path')[0]
                map_layer.insertBefore(self.background, first_path)
                self.background_inserted = True

            for map_node in map_layer.childNodes:
                if (map_node.nodeName in ('g', 'path', 'polygon') and map_node.getAttribute('id') == '_{}'.format(loc.lower())):

                    # Province is a polygon - Setting influence directly
                    if map_node.nodeName in ('path', 'polygon'):
                        map_node.setAttribute('class', class_name)

                        dup_node = map_node.cloneNode(False)
                        dup_node.setAttribute('fill', '#FFFFFF')
                        dup_node.removeAttribute('class')
                        dup_node.setAttribute('id', f"{dup_node.getAttribute('id')}_back")

                        self.background.appendChild(dup_node)
                        map_node.setAttribute('opacity', str(self.opacities[class_name]))
                        return xml_map

                    # Otherwise, map node is a 'g' node.
                    node_edited = False
                    for sub_node in map_node.childNodes:
                        if sub_node.nodeName in ('path', 'polygon') and sub_node.getAttribute('class') != 'water':
                            node_edited = True
                            sub_node.setAttribute('class', class_name)

                            dup_node = sub_node.cloneNode(False)
                            dup_node.setAttribute('fill', '#FFFFFF')
                            dup_node.removeAttribute('class')
                            dup_node.setAttribute('id', f"{dup_node.getAttribute('id')}_back")

                            self.background.appendChild(dup_node)
                            sub_node.setAttribute('opacity', str(self.opacities[class_name]))
                    if node_edited:
                        return xml_map

        # Returning
        return xml_map

    def custom_center_symbol_around_unit(self, loc, is_dislodged, symbol, weight=1):
        """ Compute top-left coordinates of a symbol to be centered around a unit.

            :param loc: unit location (e.g. 'PAR')
            :param is_dislodged: boolean to tell if unit is dislodged
            :param symbol: symbol identifier (e.g. 'HoldUnit')
            :return: a couple of coordinates (x, y) as string values
        """
        key = 'disl' if is_dislodged else 'unit'
        unit_x, unit_y = self.metadata['coord'][loc][key]
        unit_height, unit_width = self.metadata['symbol_size'][ARMY]
        symbol_height, symbol_width = (str(float(size) * CustomRenderer.scale_weight(weight)) for size in self.metadata['symbol_size'][symbol])
        return (
            str(float(unit_x) + float(unit_width) / 2 - float(symbol_width) / 2),
            str(float(unit_y) + float(unit_height) / 2 - float(symbol_height) / 2)
        )

    def custom_issue_hold_order(self, xml_map, loc, power_name, weight=1):
        """ Adds a hold order to the map

            :param xml_map: The xml map being generated
            :param loc: The province where the unit is holding (e.g. 'PAR')
            :param power_name: The name of the power owning the unit
            :return: Nothing
        """
        # Symbols
        symbol = 'HoldUnit'
        loc_x, loc_y = self.custom_center_symbol_around_unit(loc, False, symbol, weight)

        # Creating nodes
        g_node = xml_map.createElement('g')
        g_node.setAttribute('stroke', self.metadata['color'][power_name])
        CustomRenderer.apply_weight_opacity(g_node, weight)
        symbol_node = xml_map.createElement('use')
        symbol_node.setAttribute('x', loc_x)
        symbol_node.setAttribute('y', loc_y)
        symbol_node.setAttribute('height', str(float(self.metadata['symbol_size'][symbol][0]) * CustomRenderer.scale_weight(weight)))
        symbol_node.setAttribute('width', str(float(self.metadata['symbol_size'][symbol][1]) * CustomRenderer.scale_weight(weight)))
        symbol_node.setAttribute('xlink:href', '#{}'.format(symbol))

        # Inserting
        g_node.appendChild(symbol_node)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer1':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def custom_issue_move_order(self, xml_map, src_loc, dest_loc, power_name, weight=1):
        """ Issues a move order

            :param xml_map: The xml map being generated
            :param src_loc: The location where the unit is moving from (e.g. 'PAR')
            :param dest_loc: The location where the unit is moving to (e.g. 'MAR')
            :param power_name: The power name issuing the move order
            :return: Nothing
        """
        is_dislodged = self.game.get_current_phase()[-1] == 'R'
        src_loc_x, src_loc_y = self._get_unit_center(src_loc, is_dislodged)
        dest_loc_x, dest_loc_y = self._get_unit_center(dest_loc, is_dislodged)

        # Adjusting destination
        delta_x = dest_loc_x - src_loc_x
        delta_y = dest_loc_y - src_loc_y
        vector_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
        delta_dec = float(self.metadata['symbol_size'][ARMY][1]) / 2 + 2 * self._colored_stroke_width()
        dest_loc_x = str(round(src_loc_x + (vector_length - delta_dec) / vector_length * delta_x, 2))
        dest_loc_y = str(round(src_loc_y + (vector_length - delta_dec) / vector_length * delta_y, 2))

        src_loc_x = str(src_loc_x)
        src_loc_y = str(src_loc_y)
        dest_loc_x = str(dest_loc_x)
        dest_loc_y = str(dest_loc_y)

        # Creating nodes
        g_node = xml_map.createElement('g')
        g_node.setAttribute('stroke', self.metadata['color'][power_name])
        CustomRenderer.apply_weight_opacity(g_node, weight)

        line_with_shadow = xml_map.createElement('line')
        line_with_shadow.setAttribute('x1', src_loc_x)
        line_with_shadow.setAttribute('y1', src_loc_y)
        line_with_shadow.setAttribute('x2', dest_loc_x)
        line_with_shadow.setAttribute('y2', dest_loc_y)
        line_with_shadow.setAttribute('class', 'varwidthshadow')
        line_with_shadow.setAttribute('stroke-width', str(self._plain_stroke_width()))

        line_with_arrow = xml_map.createElement('line')
        line_with_arrow.setAttribute('x1', src_loc_x)
        line_with_arrow.setAttribute('y1', src_loc_y)
        line_with_arrow.setAttribute('x2', dest_loc_x)
        line_with_arrow.setAttribute('y2', dest_loc_y)
        line_with_arrow.setAttribute('class', 'varwidthorder')
        line_with_arrow.setAttribute('stroke', self.metadata['color'][power_name])
        line_with_arrow.setAttribute('stroke-width', str(self._colored_stroke_width() * CustomRenderer.scale_weight(weight)))
        line_with_arrow.setAttribute('marker-end', 'url(#arrow)')

        # Inserting
        g_node.appendChild(line_with_shadow)
        g_node.appendChild(line_with_arrow)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer1':
                        layer_node.appendChild(g_node)
                        return xml_map

    def custom_issue_support_hold_order(self, xml_map, loc, dest_loc, power_name, weight=1):
        """ Issues a support hold order

            :param xml_map: The xml map being generated
            :param loc: The location of the unit sending support (e.g. 'BER')
            :param dest_loc: The location where the unit is holding from (e.g. 'PAR')
            :param power_name: The power name issuing the move order
            :return: Nothing
        """
        # Symbols
        symbol = 'SupportHoldUnit'
        symbol_loc_x, symbol_loc_y = self.custom_center_symbol_around_unit(dest_loc, False, symbol, weight)
        symbol_node = xml_map.createElement('use')
        symbol_node.setAttribute('x', symbol_loc_x)
        symbol_node.setAttribute('y', symbol_loc_y)
        symbol_node.setAttribute('height', str(float(self.metadata['symbol_size'][symbol][0]) * CustomRenderer.scale_weight(weight)))
        symbol_node.setAttribute('width', str(float(self.metadata['symbol_size'][symbol][1]) * CustomRenderer.scale_weight(weight)))
        symbol_node.setAttribute('xlink:href', '#{}'.format(symbol))

        loc_x, loc_y = self._get_unit_center(loc, False)
        dest_loc_x, dest_loc_y = self._get_unit_center(dest_loc, False)

        # Adjusting destination
        delta_x = dest_loc_x - loc_x
        delta_y = dest_loc_y - loc_y
        vector_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
        delta_dec = float(self.metadata['symbol_size'][symbol][1]) / 2
        dest_loc_x = round(loc_x + (vector_length - delta_dec) / vector_length * delta_x, 2)
        dest_loc_y = round(loc_y + (vector_length - delta_dec) / vector_length * delta_y, 2)

        # Creating nodes
        g_node = xml_map.createElement('g')
        g_node.setAttribute('stroke', self.metadata['color'][power_name])
        CustomRenderer.apply_weight_opacity(g_node, weight)

        shadow_line = xml_map.createElement('line')
        shadow_line.setAttribute('x1', str(loc_x))
        shadow_line.setAttribute('y1', str(loc_y))
        shadow_line.setAttribute('x2', str(dest_loc_x))
        shadow_line.setAttribute('y2', str(dest_loc_y))
        shadow_line.setAttribute('class', 'shadowdash')

        support_line = xml_map.createElement('line')
        support_line.setAttribute('x1', str(loc_x))
        support_line.setAttribute('y1', str(loc_y))
        support_line.setAttribute('x2', str(dest_loc_x))
        support_line.setAttribute('y2', str(dest_loc_y))
        support_line.setAttribute('class', 'supportorder')

        # Inserting
        g_node.appendChild(shadow_line)
        g_node.appendChild(support_line)
        g_node.appendChild(symbol_node)

        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer2':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def custom_issue_support_move_order(self, xml_map, loc, src_loc, dest_loc, power_name, weight):
        """ Issues a support move order

            :param xml_map: The xml map being generated
            :param loc: The location of the unit sending support (e.g. 'BER')
            :param src_loc: The location where the unit is moving from (e.g. 'PAR')
            :param dest_loc: The location where the unit is moving to (e.g. 'MAR')
            :param power_name: The power name issuing the move order
            :return: Nothing
        """
        loc_x, loc_y = self._get_unit_center(loc, False)
        src_loc_x, src_loc_y = self._get_unit_center(src_loc, False)
        dest_loc_x, dest_loc_y = self._get_unit_center(dest_loc, False)

        # Adjusting destination
        delta_x = dest_loc_x - src_loc_x
        delta_y = dest_loc_y - src_loc_y
        vector_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
        delta_dec = float(self.metadata['symbol_size'][ARMY][1]) / 2 + 2 * self._colored_stroke_width()
        dest_loc_x = str(round(src_loc_x + (vector_length - delta_dec) / vector_length * delta_x, 2))
        dest_loc_y = str(round(src_loc_y + (vector_length - delta_dec) / vector_length * delta_y, 2))

        # Creating nodes
        g_node = xml_map.createElement('g')
        CustomRenderer.apply_weight_opacity(g_node, weight)

        path_with_shadow = xml_map.createElement('path')
        path_with_shadow.setAttribute('class', 'shadowdash')
        path_with_shadow.setAttribute('d', 'M {x},{y} C {src_x},{src_y} {src_x},{src_y} {dest_x},{dest_y}'
                                      .format(x=loc_x,
                                              y=loc_y,
                                              src_x=src_loc_x,
                                              src_y=src_loc_y,
                                              dest_x=dest_loc_x,
                                              dest_y=dest_loc_y))

        path_with_arrow = xml_map.createElement('path')
        path_with_arrow.setAttribute('class', 'supportorder')
        path_with_arrow.setAttribute('stroke-width', str(self._colored_stroke_width() * 8 * CustomRenderer.scale_weight(weight)))
        path_with_arrow.setAttribute('stroke', self.metadata['color'][power_name])
        path_with_arrow.setAttribute('marker-end', 'url(#arrow)')
        path_with_arrow.setAttribute('d', 'M {x},{y} C {src_x},{src_y} {src_x},{src_y} {dest_x},{dest_y}'
                                     .format(x=loc_x,
                                             y=loc_y,
                                             src_x=src_loc_x,
                                             src_y=src_loc_y,
                                             dest_x=dest_loc_x,
                                             dest_y=dest_loc_y))

        # Inserting
        g_node.appendChild(path_with_shadow)
        g_node.appendChild(path_with_arrow)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer2':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def custom_issue_convoy_order(self, xml_map, loc, src_loc, dest_loc, power_name, weight):
        """ Issues a convoy order

            :param xml_map: The xml map being generated
            :param loc: The location of the unit convoying (e.g. 'BER')
            :param src_loc: The location where the unit being convoyed is moving from (e.g. 'PAR')
            :param dest_loc: The location where the unit being convoyed is moving to (e.g. 'MAR')
            :param power_name: The power name issuing the convoy order
            :return: Nothing
        """
        symbol = 'ConvoyTriangle'
        symbol_loc_x, symbol_loc_y = self.custom_center_symbol_around_unit(src_loc, False, symbol, weight)
        symbol_height = float(self.metadata['symbol_size'][symbol][0]) * CustomRenderer.scale_weight(weight)
        symbol_width = float(self.metadata['symbol_size'][symbol][1]) * CustomRenderer.scale_weight(weight)
        triangle = EquilateralTriangle(x_top=float(symbol_loc_x) + symbol_width / 2,
                                       y_top=float(symbol_loc_y),
                                       x_right=float(symbol_loc_x) + symbol_width,
                                       y_right=float(symbol_loc_y) + symbol_height,
                                       x_left=float(symbol_loc_x),
                                       y_left=float(symbol_loc_y) + symbol_height)
        symbol_loc_y = str(float(symbol_loc_y) - float(self.metadata['symbol_size'][symbol][0]) / 6)

        loc_x, loc_y = self._get_unit_center(loc, False)
        src_loc_x, src_loc_y = self._get_unit_center(src_loc, False)
        dest_loc_x, dest_loc_y = self._get_unit_center(dest_loc, False)

        # Adjusting starting arrow (from convoy to start location)
        # This is to avoid the end of the arrow conflicting with the convoy triangle
        src_loc_x_1, src_loc_y_1 = triangle.intersection(loc_x, loc_y)
        src_loc_x_1 = str(src_loc_x_1)
        src_loc_y_1 = str(src_loc_y_1)

        # Adjusting destination arrow (from start location to destination location)
        # This is to avoid the start of the arrow conflicting with the convoy triangle
        src_loc_x_2, src_loc_y_2 = triangle.intersection(dest_loc_x, dest_loc_y)
        src_loc_x_2 = str(src_loc_x_2)
        src_loc_y_2 = str(src_loc_y_2)

        # Adjusting destination arrow (from start location to destination location)
        # This is to avoid the start of the arrow conflicting with the convoy triangle
        dest_delta_x = dest_loc_x - src_loc_x
        dest_delta_y = dest_loc_y - src_loc_y
        dest_vector_length = (dest_delta_x ** 2 + dest_delta_y ** 2) ** 0.5
        delta_dec = float(self.metadata['symbol_size'][ARMY][1]) / 2 + 2 * self._colored_stroke_width()
        dest_loc_x = str(round(src_loc_x + (dest_vector_length - delta_dec) / dest_vector_length * dest_delta_x, 2))
        dest_loc_y = str(round(src_loc_y + (dest_vector_length - delta_dec) / dest_vector_length * dest_delta_y, 2))

        loc_x = str(loc_x)
        loc_y = str(loc_y)

        # Generating convoy triangle node
        symbol_node = xml_map.createElement('use')
        symbol_node.setAttribute('x', symbol_loc_x)
        symbol_node.setAttribute('y', symbol_loc_y)
        symbol_node.setAttribute('height', self.metadata['symbol_size'][symbol][0])
        symbol_node.setAttribute('width', self.metadata['symbol_size'][symbol][1])
        symbol_node.setAttribute('xlink:href', '#{}'.format(symbol))

        # Creating nodes
        g_node = xml_map.createElement('g')
        g_node.setAttribute('stroke', self.metadata['color'][power_name])
        CustomRenderer.apply_weight_opacity(g_node, weight)

        src_shadow_line = xml_map.createElement('line')
        src_shadow_line.setAttribute('x1', loc_x)
        src_shadow_line.setAttribute('y1', loc_y)
        src_shadow_line.setAttribute('x2', src_loc_x_1)
        src_shadow_line.setAttribute('y2', src_loc_y_1)
        src_shadow_line.setAttribute('class', 'shadowdash')

        src_convoy_line = xml_map.createElement('line')
        src_convoy_line.setAttribute('x1', loc_x)
        src_convoy_line.setAttribute('y1', loc_y)
        src_convoy_line.setAttribute('x2', src_loc_x_1)
        src_convoy_line.setAttribute('y2', src_loc_y_1)
        src_convoy_line.setAttribute('class', 'convoyorder')

        dest_shadow_line = xml_map.createElement('line')
        dest_shadow_line.setAttribute('x1', src_loc_x_2)
        dest_shadow_line.setAttribute('y1', src_loc_y_2)
        dest_shadow_line.setAttribute('x2', dest_loc_x)
        dest_shadow_line.setAttribute('y2', dest_loc_y)
        dest_shadow_line.setAttribute('class', 'shadowdash')

        dest_convoy_line = xml_map.createElement('line')
        dest_convoy_line.setAttribute('x1', src_loc_x_2)
        dest_convoy_line.setAttribute('y1', src_loc_y_2)
        dest_convoy_line.setAttribute('x2', dest_loc_x)
        dest_convoy_line.setAttribute('y2', dest_loc_y)
        dest_convoy_line.setAttribute('class', 'convoyorder')
        dest_convoy_line.setAttribute('marker-end', 'url(#arrow)')

        # Inserting
        g_node.appendChild(src_shadow_line)
        g_node.appendChild(dest_shadow_line)
        g_node.appendChild(src_convoy_line)
        g_node.appendChild(dest_convoy_line)
        g_node.appendChild(symbol_node)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer2':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map
