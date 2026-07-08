import ETL.odd_scrapper as odd
import pandas as pd

# Premier Extracter

premier = odd.composter('https://lat.betano.com/sport/futbol/inglaterra/premier-league/1/')
premier_csv = premier.to_csv('Odd_Premier.csv', index = False) 

# La Liga Extract

laliga = odd.composter('https://lat.betano.com/sport/futbol/espana/laliga/5/')
laliga_csv = laliga.to_csv('Odd_LaLiga.csv', index = False)

# Bundes

bundesliga = odd.composter('https://lat.betano.com/sport/futbol/alemania/bundesliga/216/')
bundes_csv = bundesliga.to_csv('Odd_Bundesliga.csv', index = False)

# Seria A

seria_a = odd.composter('https://lat.betano.com/sport/futbol/italia/serie-a/1635/')
seria_csv = seria_a.to_csv('Odd_SeriaA.csv', index = False)


