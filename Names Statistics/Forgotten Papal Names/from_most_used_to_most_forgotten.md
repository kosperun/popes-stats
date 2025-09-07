[Top 15 Papal Names From Popular to Neglected](https://github.com/user-attachments/assets/7424bb38-830f-4ec5-af70-ee0b81adccf7)

With a lifelong interest in the history of the Papacy, I wanted to visualize which papal names were once popular but later fell out of use. To measure this, I created a simple metric:

`Neglect Score = (Current Year − Year of Last Usage) × Number of Times Used`

This combines how often a name was chosen with how long it has been since it last appeared.

Simply counting years since last use is unrepresentative: both Sergius and Stephen haven’t been used since roughly the same era (1012 and 1058). But there were 9 popes named Stephen compared to just 4 Sergius, so if we only looked at regular years since last use, they would look equally neglected, while factoring in historical popularity shows Stephen as much more abandoned.

The animation above shows, across history, the top 15 most-used papal names and how long each had been "neglected" at that point in time.

Retrospectively, this chart reflects the classification of popes as recognized today: for example, John XXIII of the 15th century was considered a legitimate pope until 1958, which affects how historical neglect is measured. Under this retrospective view, the most popular papal name, John, appears highly neglected for 400 years (from the mid-16th century until Cardinal Roncalli chose the name John XXIII in 1958).  

The table below lists all papal names (used more than once) sorted by their neglect score in 2013:

|# | Name     | Times Used | Year Last Used | Neglect Score    |
|:---:|:----------:|:-----------------:|:----------------:|:----------:|
| 1 | Stephen | 9 | 1058 | 8700.81 |
| 2 | Boniface | 8 | 1404 | 4962.00 |
| 3 | Felix | 3 | 530 | 4482.83 |
| 4 | Sergius | 4 | 1012 | 4050.55 |
| 5 | Innocent | 13 | 1724 | 3910.62 |
| 6 | Celestine | 5 | 1296 | 3650.25 |
| 7 | Clement | 14 | 1774 | 3503.86 |
| 8 | Anastasius | 4 | 1154 | 3480.31 |
| 9 | Urban | 8 | 1644 | 3043.39 |
| 10 | Adrian | 6 | 1523 | 3007.79 |
| 11 | Honorius | 4 | 1287 | 2950.98 |
| 12 | Sylvester | 3 | 1063 | 2939.43 |
| 13 | Pelagius | 2 | 590 | 2869.80 |
| 14 | Gregory | 16 | 1846 | 2857.33 |
| 15 | Nicholas | 5 | 1455 | 2848.85 |
| 16 | Victor | 3 | 1087 | 2811.88 |
| 17 | Adeodatus | 2 | 676 | 2697.08 |
| 18 | Lucius | 3 | 1185 | 2517.30 |
| 19 | Alexander | 7 | 1691 | 2337.42 |
| 20 | Eugene | 4 | 1447 | 2311.43 |
| 21 | Theodore | 2 | 897 | 2254.06 |
| 22 | Sixtus | 5 | 1590 | 2171.73 |
| 23 | Marinus | 2 | 946 | 2157.33 |
| 24 | Agapetus | 2 | 955 | 2138.30 |
| 25 | Damasus | 2 | 1048 | 1952.79 |
| 26 | Paschal | 2 | 1118 | 1813.89 |
| 27 | Gelasius | 2 | 1119 | 1811.85 |
| 28 | Martin | 3 | 1431 | 1781.59 |
| 29 | Callixtus | 3 | 1458 | 1699.21 |
| 30 | Leo | 13 | 1903 | 1578.82 |
| 31 | Julius | 3 | 1555 | 1409.27 |
| 32 | John | 21 | 1963 | 1293.14 |
| 33 | Marcellus | 2 | 1555 | 939.33 |
| 34 | Pius | 12 | 1958 | 794.74 |
| 35 | Paul | 6 | 1978 | 278.42 |
| 36 | Benedict | 15 | 2013 | 177.64 |
| 37 | John Paul | 2 | 2005 | 39.49 |

Data source: <https://en.wikipedia.org/wiki/List_of_popes>

Tools: Python, pandas, bar_chart_race
