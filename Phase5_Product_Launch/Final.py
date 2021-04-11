#importing necessary libraries
import pandas as pd
import numpy as np
import geopy
import geopandas
from geopy import Nominatim
#import folium
import requests
import json
#import gmaps
import osmnx as ox
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio

# Defining the map boundaries 
north, east, south, west = 44.047432, -78.787944, 43.832065, -78.958772  
# Downloading the map as a graph object 
G = ox.graph_from_bbox(north, south, east, west, network_type = 'drive') 

from flask import Flask,render_template,request, url_for, redirect
app = Flask(__name__)
#load the dataset
df = pd.read_csv('addresses-Canada.csv')

#merging the features of the address
df['ADDRESS']=df['Address 1']+","+df['City']+","+df['City']+","+df['Province']+","+df['Country']


#Converting address to latitude and longitude
from geopy.extra.rate_limiter import RateLimiter
locator = Nominatim(user_agent='nandinimalhotra04@gmail.com')
# 1 - conveneint function to delay between geocoding calls
geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
# 2- - create location column
df['location'] = df['ADDRESS'].apply(geocode)
# 3 - create longitude, laatitude and altitude from location column (returns tuple)
df['point'] = df['location'].apply(lambda loc: tuple(loc.point) if loc else None)
# 4 - split point column into latitude, longitude and altitude columns
df[['latitude', 'longitude', 'altitude']] = pd.DataFrame(df['point'].tolist(), index=df.index)


#Dropping irrelevant features
df = df.drop(['Address 1', 'City', 'Province', 'Country','Postal Code','Telefon', 'ADDRESS', 'location', 'point','Number','altitude'], axis=1)
# Dropping missing values
df.dropna(subset = ["latitude","longitude"], inplace=True)


#---------------------------------------------------------------
@app.route('/')
def default():
   return render_template('home.html')

@app.route('/Calculate Route',methods=['GET','POST'])
def home():
    if request.method=='POST':
      data2=request.form.getlist('Category')
      data1=request.form['address']
      #Calculating user latitude and longitude
     #Calculating user latitude and longitude
      length=len(data2)
      print(length)
      user_locator = Nominatim(user_agent='nandinimalhotra04@gmail.com')
      user_location = user_locator.geocode(data1)
      #Storing the user latitude and longitude in the variables
      user_latitude=user_location[-1][0]
      user_longitude=user_location[-1][1]
      #Filtering the dataset so as to keep just the categories that are to be visited
      df_narrowed=df[df['Category'].isin(data2)].reset_index(drop=True)
      # Creating a new dataset that will contain the final destination
      data=[['User','Home Address',user_latitude,user_longitude,0,'pink','male']]
      df_short = pd.DataFrame(data, columns = ['Category','Name','latitude','longitude','Distance(km)','color','shape'])
      
      #-------------------------------------------
      #AI Agent
      for j in range(len(data2)):
          df_narrowed['Distance']=0
          for i in range(len(df_narrowed)):
              # call the OSMR API
              r = requests.get(f"http://router.project-osrm.org/route/v1/car/{df_narrowed.longitude[i]},{df_narrowed.latitude[i]};{df_short.longitude[j]},{df_short.latitude[j]}?overview=false""")
                # then you load the response using the json libray
                # by default you get only one alternative so you access 0-th element of the `routes`
              results = json.loads(r.content)
              legs = results.get("routes").pop(0).get("legs")
              df_narrowed.Distance[i]=legs[0].get("distance")
          df_narrowed['Distance(km)']=df_narrowed['Distance']/1000
          df_narrowed=df_narrowed.sort_values('Distance(km)').reset_index(drop=True)
            # print("Data frame with distance")
            # display(df_narrowed)
        
            
            #Filter the required fields for the nearest store and storing it in the dataste to be appended in df_short
          df_temp=df_narrowed[['Category','Name','latitude','longitude','Distance(km)','color','shape']][0:1]
          category_id=df_temp['Category'][0]
#            print(category_id)
#            print("Optimal Path Dataset")
          df_short=df_short.append(df_temp).reset_index(drop=True)
            #display(df_short)
        
            
            #Filtering the dataset so as to keep just the categories that are to be visited
          df_narrowed=df_narrowed.drop(df_narrowed[df_narrowed['Category']==category_id].index).reset_index(drop=True)
          if(len(df_narrowed)!=0):
              #print("\nFiltered dataset for next destination")
              df_narrowed=df_narrowed.drop(['Distance','Distance(km)'],axis=1)
                #display(df_narrowed)
                
            #-------------------------------------
    
    
    def plot_path(lat, long, origin_point, destination_point,name_categ_source,name_categ_dest,count):
    
            """
            Given a list of latitudes and longitudes, origin 
            and destination point, plots a path on a map

            Parameters
            ----------
            lat, long: list of latitudes and longitudes
            origin_point, destination_point: co-ordinates of origin
            and destination    Returns
            -------
            Nothing. Only shows the map.
            """    # adding the lines joining the nodes
            fig = go.Figure(go.Scattermapbox(
                name = "Path",
                mode = "lines",
                lon = long,
                lat = lat,
                marker = {'size': 10},
                line = dict(width = 4.5, color = 'blue')))    # adding source marker
            fig.add_trace(go.Scattermapbox(
                name = "Source: "+name_categ_source[0],
                mode = 'markers',
                textposition='top right',
                textfont=dict(size=16, color='black'),
                text=[name_categ_source[0] + '<br>' + name_categ_source[1]],
                lon = [origin_point[1]],
                lat = [origin_point[0]],
                marker = {'size': 12, 'color':"red"}))

            # adding destination marker
            fig.add_trace(go.Scattermapbox(
                name = "Destination: "+name_categ_dest[0],
                mode = 'markers',
                textposition='top right',
                textfont=dict(size=16, color='black'),
                text=[name_categ_dest[0] + '<br>' + name_categ_dest[1]],
                lon = [destination_point[1]],
                lat = [destination_point[0]],
                marker = {'size': 12, 'color':'green'}))

            # getting center for plots:
            lat_center = np.mean(lat)
            long_center = np.mean(long)    # defining the layout using mapbox_style
            fig.update_layout(mapbox_style="stamen-terrain",
                mapbox_center_lat = 30, mapbox_center_lon=-80)
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                              mapbox = {
                                  'center': {'lat': lat_center, 
                                  'lon': long_center},
                                  'zoom': 13})
            print('Image saved')
            pio.write_html(fig, 'templates/map_'+str(count)+'.html')
            
            #saving as image
            #pio.write_image(fig, 'static/map_'+str(count)+'.webp')
            #fig.show()
            
    def node_list_to_path(G, node_list):
        """
        Given a list of nodes, return a list of lines that together
        follow the path
        defined by the list of nodes.
        Parameters
        ----------
        G : networkx multidigraph
        route : list
            the route as a list of nodes
        Returns
        -------
        lines : list of lines given as pairs ( (x_start, y_start), 
        (x_stop, y_stop) )
        """
        edge_nodes = list(zip(node_list[:-1], node_list[1:]))
        lines = []
        for u, v in edge_nodes:
            # if there are parallel edges, select the shortest in length
            data = min(G.get_edge_data(u, v).values(), 
                       key=lambda x: x['length'])
            # if it has a geometry attribute
            if 'geometry' in data:
                # add them to the list of lines to plot
                xs, ys = data['geometry'].xy
                lines.append(list(zip(xs, ys)))
            else:
                # if it doesn't have a geometry attribute,
                # then the edge is a straight line from node to node
                x1 = G.nodes[u]['x']
                y1 = G.nodes[u]['y']
                x2 = G.nodes[v]['x']
                y2 = G.nodes[v]['y']
                line = [(x1, y1), (x2, y2)]
                lines.append(line)
        return lines

    count=0
    for j in range(len(df_short)):
        if j+1<=len(df_short)-1:
            origin_point = (df_short.latitude[j], df_short.longitude[j]) 
            destination_point = (df_short.latitude[j+1], df_short.longitude[j+1])
            name_categ_source= (df_short.Name[j], df_short.Category[j])
            name_categ_dest = (df_short.Name[j+1], df_short.Category[j+1])
    #         print('Origin',origin_point)
    #         print(destination_point)
            # get the nearest nodes to the locations 
            origin_node = ox.get_nearest_node(G, origin_point) 
            destination_node = ox.get_nearest_node(G, destination_point)
            # printing the closest node id to origin and destination points 
            origin_node, destination_node
            route = nx.shortest_path(G, origin_node, destination_node, weight = 'length')
            #print(route)
            # getting coordinates of the nodes
    # we will store the longitudes and latitudes in following list 
            long = [] 
            lat = []  
            for i in route:
                point = G.nodes[i]
                long.append(point['x'])
                lat.append(point['y'])
                #print(lat,long)    
            
                # getting the list of coordinates from the path 
        # (which is a list of nodes)
            lines = node_list_to_path(G, route)
            long2 = []
            lat2 = []
            for i in range(len(lines)):
                z = list(lines[i])
                l1 = list(list(zip(*z))[0])
                l2 = list(list(zip(*z))[1])
                for j in range(len(l1)):
                    long2.append(l1[j])
                    lat2.append(l2[j])
            count+=1        
            plot_path(lat2, long2, origin_point, destination_point,name_categ_source,name_categ_dest,count)
            #return redirect(url_for('home'))
    file_name=['map_1.html','map_2.html','map_3.html','map_4.html','map_5.html']
    return render_template('result.html',value1=data1,value2=len(data2),maps=file_name)

if __name__ == "__main__":
    app.run(debug=True)
