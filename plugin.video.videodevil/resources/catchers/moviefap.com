########################################################
#                Moviefap VideoCatcher                 #
########################################################
url=%s
target=flashvars.config = escape."([^ ]+)VID=
forward=True
########################################################
url=%s
target=<videoLink>(.+?)</videoLink>
quality=standard
build=%s
########################################################
