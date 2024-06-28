import os

class Splitter:
    def __init__(self, src_path, dest_path, split_points=[0.9, 1], split_names=["train.jsonl", "test.jsonl"], total_games=1000):
        self.src_path = src_path
        self.dest_path = dest_path
        self.split_points = split_points
        self.split_names = split_names
        self.total_games = total_games
    
    def split(self):
        write_files = list()
        for name in self.split_names:
            filename = os.path.join(self.dest_path, name)
            write_files.append(open(filename, 'w'))

        with open(self.src_path, 'r') as src:
            for n, line in enumerate(src):
                for s, split in enumerate(self.split_points):
                    if n < split * self.total_games:
                        write_files[s].write(line)
                        print(f"Writing line {n} in set {self.split_names[s]}")
                        break
                if n >= self.total_games:
                    break

        for file in write_files:
            file.close()

if __name__ == "__main__":
    src_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "standard_no_press.jsonl")
    dest_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
    splitter = Splitter(src_path, dest_path)
    splitter.split()