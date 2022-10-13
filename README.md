# pop-spider
Wikipedia scraper for retrieving Billboard year-end lists


## Installation / Setup

1. Install Anaconda, if it hasn't already been installed yet.

2. Create environment in Anaconda, in Python 3.9, and install libraries:

```
> conda create -n popspider python=3.9

> conda activate popspider

> pip install -r requirements.txt
```

That should install Scrapy version 2.6 to the newly created Anaconda envuronment.

To run the spider, go to the `pop-spider` base directory and run:

```
> scrapy crawl yearendlists -O output.csv
```

This command runs the spider found at: `popspider/spiders/yearendlists.py` and saves the output to file `output.py` in the same directory the command was run.  Git should ignore this output file.