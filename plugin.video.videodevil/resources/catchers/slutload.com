########################################################
#                Slutload VideoCatcher                 #
########################################################
url=%s
target=id="vidPlayer"\s+data-url="([^"]+slutload-media.com[^"]+)"
extension=mp4
quality=standard
build=%s
########################################################
