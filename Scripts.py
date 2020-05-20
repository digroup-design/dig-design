import calculations.AddressQueryFactory as Q

q = Q.AddressQueryFactory()
data = q.get(city="San Diego", state="CA", address="2405 union st")

with open("test.csv", 'w', newline='') as f:
    Q.dict_to_csv(data, f, delimiter=',')

