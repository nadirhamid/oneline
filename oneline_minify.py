from slimit.minifier import minify

noticeOfCopyright = open("./js/copyright_tag", "r").read()

files = ['./js/bson.js', './js/transport.js', './js/oneline.js']
minifiedString = ""
for i in files:
  thisFileContents = open(i, "r").read()
  minified = minify(thisFileContents, mangle=True, mangle_toplevel=True) 
  minifiedString += minified


output = noticeOfCopyright + minifiedString
file = open("./js/oneline.min.js", "w+")
file.write(output)
file.close()
