from pybaseball import batting_stats
import pandas as pd


def main():
    year = int(input('What year do you want Marcel projections for? '))
    startYr = year - 3
    middleYr = year - 2
    endYr = year - 1

    data = batting_stats(str(startYr), str(endYr), qual=100, ind=1)

    data['HR/PA'] = data['HR'] / data['PA']

    # Taking the average of all projected stats in 2021 in order to regress to the mean

    AVG_BA = data[data['Season'] == endYr]['AVG'].mean()

    AVG_SLG = data[data['Season'] == endYr]['SLG'].mean()

    AVG_OBP = data[data['Season'] == endYr]['OBP'].mean()

    AVG_hrPerPA = data[data['Season'] == endYr]['HR/PA'].mean()

    AVG_Kp = data[data['Season'] == endYr]['K%'].mean()

    # Creates projections dataframe
    proj_df = pd.DataFrame(columns={'Name': [], 'proj PA': [], '3yrPA': [], '{} AVG'.format(endYr): [],
                                    '{} AVG'.format(middleYr): [], '{} AVG'.format(startYr): [],
                                    'proj AVG': [], '{} SLG'.format(endYr): [], '{} SLG'.format(middleYr): [],
                                    '{} SLG'.format(startYr): [], 'proj SLG': [],
                                    '{} OBP'.format(endYr): [], '{} OBP'.format(middleYr): [],
                                    '{} OBP'.format(startYr): [], 'proj OBP': [], '{} HR/PA'.format(endYr): [],
                                    '{} HR/PA'.format(middleYr): [], '{} HR/PA'.format(startYr): [], 'proj HR/PA': [],
                                    '{} K%'.format(endYr): [], '{} K%'.format(middleYr): [],
                                    '{} K%'.format(startYr): [],
                                    'proj K%': [], '{} BB%'.format(endYr): [], '{} BB%'.format(middleYr): [],
                                    '{} BB%'.format(startYr): [], 'proj BB%': []})

    stats_to_regress = ['AVG', 'SLG', 'OBP', 'HR/PA', 'K%', 'BB%']

    # Only projects players with end year data
    players_endYr = []
    for k in range(len(data.Name)):
        if data['Season'][k] == endYr:
            players_endYr.append(data['Name'][k])

    proj_df['Name'] = players_endYr

    df = data[data['Name'].isin(proj_df.Name)]

    def get_stats_per_year(stat: str):
        # Loop through the players in the df which contains only the data from players
        # that played in year to be projected - 1
        index = 0
        for name in proj_df.Name:
            # Count the number of hits for the player in 2021
            name_df = df[df['Name'] == name]
            age_df = name_df[name_df['Season'] == endYr]
            avg = age_df[stat]
            proj_df['{} {}'.format(endYr, stat)][index] = avg.item()
            index += 1

        index = 0
        for name in proj_df.Name:
            # Count the number of hits for the player in 2020
            name_df = df[df['Name'] == name]
            age_df = name_df[name_df['Season'] == middleYr]
            avg = age_df['{}'.format(stat)].sum()
            proj_df.loc[index, '{} {}'.format(middleYr, stat)] = avg
            index += 1

        index = 0
        for name in proj_df.Name:
            # Count the number of hits for the player in 2019
            name_df = df[df['Name'] == name]
            age_df = name_df[name_df['Season'] == startYr]
            avg = age_df[stat].sum()
            proj_df.loc[index, '{} {}'.format(startYr, stat)] = avg
            index += 1

    def weight_stat(stat: str):
        for row in proj_df.index:
            weight = 0
            avg_end = proj_df['{} {}'.format(endYr, stat)][row]
            if avg_end > 0:
                weight += 5
            avg_mid = proj_df['{} {}'.format(middleYr, stat)][row]
            if avg_mid > 0:
                weight += 4
            avg_start = proj_df['{} {}'.format(startYr, stat)][row]
            if avg_start > 0:
                weight += 3
            if weight == 0:
                proj_df.drop(row)
            else:
                proj_df['proj {}'.format(stat)][row] = (5 * avg_end + 4 * avg_mid + 3 * avg_start) / weight

    def regress_stat(stat: str):
        if stat == 'AVG':
            CONST = data[data['Season'] == endYr]['AVG'].mean()
        elif stat == 'SLG':
            CONST = data[data['Season'] == endYr]['SLG'].mean()
        elif stat == 'OBP':
            CONST = data[data['Season'] == endYr]['OBP'].mean()
        elif stat == 'K%':
            CONST = data[data['Season'] == endYr]['K%'].mean()
        elif stat == 'BB%':
            CONST = data[data['Season'] == endYr]['BB%'].mean()
        elif stat == 'HR/PA':
            CONST = data[data['Season'] == endYr]['HR/PA'].mean()

        for row in proj_df.index:
            if proj_df['3yrPA'][row] < 1200:
                proj_df['proj {}'.format(stat)][row] = ((proj_df['proj {}'.format(stat)][row] * proj_df['3yrPA'][row]) +
                                                        (1200 - proj_df['3yrPA'][row]) * CONST) / 1200

    # if you don't have enough data (1200 pa), add the difference between abs and 1200 times average BA
    for row in proj_df.index:
        name_df = name_df = data[data['Name'] == data.Name[row]].reset_index(drop=True)
        pa = name_df['PA'].sum()
        proj_df['3yrPA'][row] = pa

    # Creates a name (key) and age (value) map for purposes of age adjustment
    name_to_age = {}
    for name in proj_df['Name']:
        name_df = df[df['Name'] == name]
        for row in name_df.index:
            if name_df['Season'][row] == endYr:
                age = name_df['Age'][row]
        name_to_age[name] = age

    for stat in stats_to_regress:
        get_stats_per_year(stat)
        weight_stat(stat)
        regress_stat(stat)

    for row in proj_df.index:
        name_df = df[df['Name'] == proj_df.Name[row]]
        season_end = name_df[name_df['Season'] == endYr]
        season_mid = name_df[name_df['Season'] == middleYr]
        pa_end = season_end['PA'].item()
        if season_mid.empty:
            pa_mid = 0
        else:
            pa_mid = season_mid['PA'].item()
        proj_PA = (0.5 * pa_end) + (0.1 * pa_mid) + 200
        proj_df['proj PA'][row] = round(proj_PA, 0)

    index = 0
    for name in proj_df['Name']:
        if name_to_age[name] >= 29:
            proj_df['proj PA'][index] -= (name_to_age[name] - 29) * .003
            index += 1
        else:
            proj_df['proj PA'][index] -= (name_to_age[name] - 29) * .006
            index += 1

    for row in proj_df.index:
        proj_df['proj PA'][row] = round(proj_df['proj PA'][row], 0)

    print(proj_df)


if __name__ == main():
    main()
