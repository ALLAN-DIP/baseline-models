from xml.dom import minidom

from diplomacy.engine.renderer import Renderer, _attr
from utils import OrderEnum


class CustomRenderer(Renderer):

    def __init__(self, game, svg_path=None):
        super().__init__(game, svg_path)

        self.order_dict = {
            OrderEnum.NO_ORDER: None,
            OrderEnum.HOLD_ORDER: self._issue_hold_order,
            OrderEnum.MOVE_ORDER: self._issue_move_order,
            OrderEnum.SUPPORT_MOVE_ORDER: self._issue_support_move_order,
            OrderEnum.SUPPORT_HOLD_ORDER: self._issue_hold_order,
            OrderEnum.CONVOY_ORDER: self._issue_convoy_order
        }

    # Adapted from the renderer method of the Renderer class
    def custom_render(self, incl_orders=True, incl_abbrev=False, output_format='svg', output_path=None, alterations=None):
        if output_format not in ['svg']:
            raise ValueError('Only "svg" format is current supported.')
        if not self.game or not self.game.map or not self.xml_map:
            return None

        # Parsing XML
        xml_map = minidom.parseString(self.xml_map)

        # Setting phase and note
        nb_centers = [(power.name[:3], len(power.centers))
                      for power in self.game.powers.values()
                      if not power.is_eliminated()]
        nb_centers = sorted(nb_centers, key=lambda key: key[1], reverse=True)
        nb_centers_per_power = ' '.join(['{}: {}'.format(name, centers) for name, centers in nb_centers])
        xml_map = self._set_current_phase(xml_map, self.game.get_current_phase())
        xml_map = self._set_note(xml_map, nb_centers_per_power, self.game.note)

        # Adding units and influence
        for i, power in enumerate(self.game.powers.values()):
            for unit in power.units:
                xml_map = self._add_unit(xml_map, unit, power.name, is_dislodged=False)
            for unit in power.retreats:
                xml_map = self._add_unit(xml_map, unit, power.name, is_dislodged=True)
            for center in power.centers:
                xml_map = self._set_influence(xml_map, center, power.name, has_supply_center=True)
            for loc in power.influence:
                xml_map = self._set_influence(xml_map, loc, power.name, has_supply_center=False)

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
                for order in alterations[i]:
                    order_type, order_args = self.parse_order(order, power)
                    xml_map = self.display_order(order_type, order_args, xml_map)

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
