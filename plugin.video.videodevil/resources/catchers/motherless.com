########################################################
#               Motherless VideoCatcher                #
########################################################
url=%s
target=fileurl = '([^']+flv)'
quality=standard
build=%s?start=0
########################################################
