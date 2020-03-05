# CapTube  
A tool which can capture a Youtube video into images that you can read the video fastly.  
  
## Usage  
  
```  
./run.py -u <Youtube url> -n <output name> -l <language>   
```  
The result files would be placed in the ./results/<output name>/*  
If the result path is already exist, but you want do it again. try again with --retry or -r option.  
Only -u option is mandatory.  
  
```  
./run.py -u <Youtube url> -n <output name> -l <language> --retry  
```  
  
For more information, please see the option --help   
  
```  
./run.py -h  
```  
  
## Example  
  
```  
./run.py -u 'https://youtu.be/MMmOLN5zBLY' -n multi_lang -l ko  
```  
  
The result would be generate like below. The captured images are in the imsg/.  
  
```  
$ ls ./results/multi_lang/  
imgs/   multi_lang.json  multi_lang.mp4   multi_lang.srt  
```  
  
## Usage of APIs  
  
Just call these functions.  
  
```  
from capture import capture_by_subs  
from run import make_youtube_info  
  
video_info = make_youtube_info(url, name, lang, retry, fontsize)  
video_info.save_json()  
capture_by_subs(video_info)  
```  
  
1. generate video information with dictionary type.  
  
```  
video_info = make_youtube_info(url, name, lang, retry, fontsize)  
```  
> argument <type>  
> url <string>: the youtube url  
> name <string>: result diretory name  
> lang <string>: language code (en, ko, ru...)  
> retry <bool>: True/False (default False)  
> fontsize <int>: default 30  
  
2. save the information to json file (if you want)  
  
```  
video_info.save_json()  
```  
> It will save name.json  
  
3. capture the video by subtitle time stamps  
  
```  
capture_by_subs(video_info)  
```  
> the results are generated in directory imgs/  

## Unit Test

```
./unit_test.py
```

