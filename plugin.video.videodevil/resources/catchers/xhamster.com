########################################################
#                Xhamster VideoCatcher                 #
########################################################
url=%s
target=srv': '([^']+)',\s+'file': '([^']+flv)',
actions=join(/key=, match, group2)
quality=standard
########################################################
target=file': '([^']+.flv[^']+)'
actions=unquote(match)
quality=standard
build=%s
########################################################
