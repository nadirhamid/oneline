## Ruby Version demonstrating streaming
## make sure you have the JSON gem!
require 'rubygems'
require 'json'

json, second = ARGV
puts JSON.parse(json)
