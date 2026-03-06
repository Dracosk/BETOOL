from ETL.odd_scrapper import betano_extract

exct_bet = betano_extract('https://lat.betano.com/sport/futbol/inglaterra/premier-league/1/')
print(exct_bet[0])
print(exct_bet[-1])
