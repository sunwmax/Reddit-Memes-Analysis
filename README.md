# r/Memes Analysis
Memes that rise to hot, and many others that die in new

# Overview
This project repo consists of three parts:
1. Data Collection (via Collector)  --> Work in progress
2. Data Analysis
3. Data Visualization

# Collector
How to use:
1. <a href = "https://www.reddit.com/prefs/apps">Apply</a> for a reddit bot
2. Apply for a local MySQL instance
3. Git clone this repo
4. Configure ```config.py```
```
USER_PARAMS = {
    "reddit": {
        "USER-AGENT": [Your reddit app user agent],
        "CLIENT-ID": [Your reddit app client id],
        "CLIENT-SECRET": [Your reddit app client secret],
    },
    "mysql-db": {
        "HOST-NAME": [Your MySQL hostname],
        "USER-NAME": [Your MySQL username],
        "USER-PASSWORD": [Your MySQL password],
    }
}
```
5. Install required dependencies
```
pip install -r requirements.txt
```
6. Run the collector
```
python main.py
```

# Analysis
(2021.7.12 New)
Sample Data is uploaded in \Analysis\Sample Data.

# Visualization
Coming soon!
