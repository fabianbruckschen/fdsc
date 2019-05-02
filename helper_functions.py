import pandas as pd
from gmaps import Polygon
from datetime import datetime, date
from haversine import haversine


# transform pandas series to timestamps
def transform_to_timestamp(string, format='%H:%M:%S'):
    return datetime.strptime(string, format).time()


# extract hour from timestamp
def extract_hour(x):
    return x.hour


# extract closest hour to timestamp
def extract_closest_hour(x):
    if x.minute > 30:
        return extract_hour(x) + 1
    else:
        return extract_hour(x)


# transform pandas coordinates to tuples for gmaps
def create_lat_long_tuples(df, colnames=['lat', 'lon']):
    return [tuple(x) for x in df[colnames].values]


# get counts on higher spatial level
def aggregate_counts(df, colnames=['lat', 'lon'],
                     digits=0, newname=None):
    return df[colnames].apply(lambda x: round(x, digits))\
                       .groupby(colnames).size()\
                       .reset_index(name=newname)


# extract polygon given two floored coordinates
def extract_polygon(df, i, level=3, color='blue',
                    latname='lat', lonname='lon'):
    row = df[(i-1):i]
    lat1 = float(row[latname])
    lon1 = float(row[lonname])
    lat2 = lat1+(1/10**level)
    lon2 = lon1+(1/10**level)

    return Polygon([(lat1, lon1), (lat1, lon2),
                    (lat2, lon2), (lat2, lon1)],
                   stroke_color=color,
                   fill_color=color)


# check if value is NaN
def isNaN(num):
    return num != num


# get difference (timedelta) of two timestamps in seconds
def get_timedelta(x):
    if isNaN(x).any():
        return 0
    else:
        return (datetime.combine(date.today(), x[0])
                - datetime.combine(date.today(), x[1])).total_seconds()


# calculate haversine distance as proxy for way travelled
def calc_distance(x, unit='m'):
    if isNaN(x).any():
        return 0
    else:
        return haversine((x[0], x[1]), (x[2], x[3]), unit=unit)


# determine zone changes of a scooter
def zone_change(x):
    if isNaN(x).any() | ((x[0] == x[2]) & (x[1] == x[3])):
        return 0
    else:
        return 1


# check if timestamp is inside timeframe
def inside_timeframe(ts, begin, end):
    return int((ts >= transform_to_timestamp(begin))
               & (ts <= transform_to_timestamp(end)))


# for 3d plotting of clusters
def create_cluster_space(df, name, color, msize=3):
    scatter = dict(mode='markers',
                   name=name,
                   type='scatter3d',
                   x=df.x, y=df.y, z=df.z,
                   marker=dict(size=msize, color=color))

    mesh = dict(alphahull=5,
                name=name,
                opacity=.1,
                type='mesh3d',
                x=df.x, y=df.y, z=df.z,
                color=color, showscale=True)
    return scatter, mesh


# allocate scooters to closest target locations
def allocate_scooters(df, targets):

    # create data frame for collection
    df_relocated = pd.DataFrame(columns=['id', 'lat_new', 'lon_new'])

    for index, row in targets.iterrows():
        # calculate distances
        df['distance'] = [haversine((x[0], x[1]), (row.lat, row.lon))
                          for x in df[['lat', 'lon']].values]
        # and rank them
        df['position'] = df.distance.rank(method='first')
        # select the n best ranks
        scooters = df[df.position <= row.n_scooters_need].id
        # stack to collecting dataframe
        df_relocated = pd.concat([df_relocated,
                                  pd.DataFrame({'id': scooters,
                                                'lat_new': row.lat,
                                                'lon_new': row.lon})])
        # and remove scooters for remaining process
        df = df[~df.id.isin(scooters)]

    return df_relocated
