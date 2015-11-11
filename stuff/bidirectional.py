
incoming = [
     dict(lat=50.00000,lng=-113.00000),
     dict(lat=20.00000,lng=-114.00000)
] 
dataset = [
     dict(lat=100.0000,lng=50.0000),
     dict(lat=60.0000, lng=10.0000),
 ] 
for i in dataset:
  for j in incoming:
    if i['lat'] <= j['lat'] and i['lat'] >= j['lat']-range and 
    i['lng'] >= j['lng'] and i['lng'] <= j['lng']+range or

    i['lat'] >= j['lat'] and i['lat'] <= j['lat']+range and
    i['lng'] <= j['lng'] and i['lng'] >= j['lng']-range or

    i['lat'] >= j['lat'] and i['lng'] <= j['lat']+range and
    i['lng'] >= j['lng'] and i['lng'] <= j['lng']+range or

    i['lat'] <= j['lat'] and i['lat'] >= i['lat']-range or
    i['lng'] >= j['lng'] and i['lng'] <=i['lng']+range:



    
    
