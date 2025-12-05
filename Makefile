youtube_ID = "XcvejCE9-7c"
#youtube_ID = "qTn75N0YJNE"
#youtube_ID = "qZr39cTvuPQ"
#youtube_ID = "PlZFODj_Mq4"
#youtube_ID = "clgbgIY_ZSw"


all:
	python demo.py

clean:
	rm -f data/transcript/*.json data/transcript/*.tsv data/transcript/*.srt
	rm -rvf CAIR.egg* build

lint:
	black *.py CAIR  --line-length 80
	flake8 *.py CAIR --ignore=E501,E712,W503
