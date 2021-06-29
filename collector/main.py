from collector import DataCollector

if __name__ == "__main__":
    collector = DataCollector()
    collector.prepare_database("memes0625")
    collector.run()