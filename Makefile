youtube_ID = "XcvejCE9-7c"
#youtube_ID = "qTn75N0YJNE"
#youtube_ID = "qZr39cTvuPQ"
#youtube_ID = "PlZFODj_Mq4"
#youtube_ID = "clgbgIY_ZSw"


all:
	python demo.py

test:
	python -m unittest -v tests.test_info_cache

clean:
	rm -f data/transcript/*.json data/transcript/*.tsv data/transcript/*.srt
	rm -rvf CAIR.egg* build

lint:
	black *.py CAIR  --line-length 80
	flake8 *.py CAIR --ignore=E501,E712,W503

test-all:
	python -m unittest discover -s tests -p "test_*.py" -v
