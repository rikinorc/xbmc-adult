########################################################
#               Kcoolonline VideoCatcher               #
########################################################
url=http://kcoolonline.com/token.php
data=url=%s
target=<a href='(.+?)' title='Download Flv Here'>
quality=standard
build=%s
########################################################
