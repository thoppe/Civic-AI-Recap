youtube_ID = "XcvejCE9-7c"
#youtube_ID = "qTn75N0YJNE"
#youtube_ID = "qZr39cTvuPQ"
youtube_ID = "PlZFODj_Mq4"
youtube_ID = "clgbgIY_ZSw"

model_id = "gpt-3.5-turbo-1106"
#model_id = "gpt-4-1106-preview"

all:
	python run_multiple.py

single:
	python cair.py --video_id $(youtube_ID) --model_name $(model_id)


add:
	git add data/metadata data/transcript/*.vtt data/transcript/*.txt
	git add data/gpt-3.5-turbo-1106
	git add data/gpt-4-1106-preview
	git add discovery/data/

clean:
	rm -f data/transcript/*.json data/transcript/*.tsv data/transcript/*.srt
	rm -rvf CAIR.egg* build

lint:
	black *.py CAIR --line-length 80
	flake8 *.py CAIR --ignore=E501,E712
