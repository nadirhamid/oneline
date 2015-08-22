from jsmin import jsmin
noticeOfCopyright = open("./js/copyright_tag", "r").read()

files = ['./js/bson.js', './js/transport.js', './js/oneline.js']
minifiedString = ""
for i in files:
  thisFileContents = open(i, "r").read()
  minified = jsmin(thisFileContents, quote_chars=r"'`\"")
  minifiedString += minified


output = noticeOfCopyright + minifiedString
file = open("./js/oneline.min.js", "w+")
file.write(output)
file.close()
