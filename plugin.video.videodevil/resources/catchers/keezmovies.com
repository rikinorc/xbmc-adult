########################################################
#               Keezmovies VideoCatcher                #
########################################################
url=%s
header=Cookie|age_verified=1
target=video_url=(http.+)[&]amp;postroll_url
quality=standard
build=%s
########################################################
