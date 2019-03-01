#! /bin/bash

DEMO_BRANCH="demo/draw_sub"
CAP_CMD="time python3 get_youtube.py"

usage() {
	echo "Usage: $0 
Options:
	-u <YouTube URL> 
	-n <out file name> 
	-l <lang coe>
	-f <font size>
	-t <git tag number>
	--no-sub" 1>&2; 
	}

# read the options
TEMP=`getopt -o hu:n:l:f:t: --long no-sub  -- "$@"`
[ $? -eq 0 ] || {
    echo "ERROR: Incorrect options provided"
    exit 1
}
eval set -- "$TEMP"

# extract options and their arguments into variables.
while true ; do
	case "$1" in
		-u)
			shift
			CAP_URL="$1"
			CAP_CMD="$CAP_CMD -u '$CAP_URL'"
			;;
		-n)
			shift
			CAP_NAME="$1"
			CAP_CMD="$CAP_CMD -n $CAP_NAME"
			;;
		-l)
			shift
			CAP_LANG="$1"
			CAP_CMD="$CAP_CMD -l $CAP_LANG"
			;;
		-f)
			shift
			CAP_FONT_SIZE="$1"
			CAP_CMD="$CAP_CMD -f $CAP_FONT_SIZE"
			;;
		-t)
			shift
			CAP_TAG_NUM=$1
			;;
		--no-sub)
			CAP_CMD="$CAP_CMD --no-sub"
			;;
		--)
			shift
			break
			;;
		*|-h)
			usage
			exit 1
			;;
	esac
	shift
done

if [ -z $CAP_TAG_NUM ] || [ -z $CAP_URL ] || [ -z $CAP_NAME ]; then
	echo " "
	echo "ERROR: Options must include all of '-u' '-n' '-t'."
	usage
	exit 1
fi


# 1. Changing git branch
git branch
git checkout $DEMO_BRANCH
git log --oneline

rm *.mp4
rm *.srt*
rm *.md
git rm *.md

echo " "
usage
echo " "
echo "--------------------------------------Make CapTube Demo----------------------------------------"
echo "Command: $CAP_CMD"
echo "Tag number: $CAP_TAG_NUM"
echo "File name: $CAP_NAME"
echo "Continue? y/n"

read CONFIRMED 

if [ $CONFIRMED == 'y' ];
then
	# 2. Do the script
	$CAP_CMD

	# NOTE: DO AFTER CONFIRMED THE BRANCH IS CREANED

	# 3. Make a commit and push to the origin
	git add $CAP_NAME.md imgs
	git commit -sm "demo $CAP_TAG_NUM $CAP_NAME"
	git tag -a "demo#$CAP_TAG_NUM" HEAD -m "$CAP_TAG_NUM $CAP_NAME"
	git push origin $DEMO_BRANCH
	git push origin --tags
	echo "Upload Done"
	exit

else
	echo "Canceled by user"
	exit
fi
echo "Canceled by user"
