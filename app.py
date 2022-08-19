#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from datetime import datetime
from jinja2 import Environment
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Creation of associated table showing connection many-to-many connection
# between Venues and Artists
venue_artists = db.Table('venue_artists',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String))
    artists = db.relationship('Artist', secondary=venue_artists,
      backref=db.backref('Venue', lazy=True))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Show',backref='venue',lazy=True, passive_deletes=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(500))
    seeking_venue= db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Show',backref='artist',lazy=True, passive_deletes=True)
  
  
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(timezone=True))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False )
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False )


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  venue_list = []

  venue_items = db.session.query(Venue).with_entities(Venue.city,Venue.state).distinct().all()

  # Loop through unique locations within the venue table
  for location in venue_items:
    location_agg = {}
    venues = []

    # Build response dict based on location
    location_agg['city'] = location.city
    location_agg['state'] = location.state

    # Find venues at the specified city and state
    filtered_venues = db.session.query(Venue).with_entities(Venue.id,Venue.name).filter(Venue.city==location.city, Venue.state==location.state).all()
    
    # Filter through venues and gather necessary details for each venue
    for venue in filtered_venues:
      venue_details = {}
  
      venue_details['id'] = venue.id
      venue_details['name'] = venue.name

      venue_shows = db.session.query(Show).with_entities(Show.id, Show.start_time).filter_by(venue_id=venue.id).distinct().all()
      upcoming_shows = []

      for show in venue_shows:

        if dateutil.parser.parse(str(show.start_time)).timestamp() < datetime.utcnow().timestamp():
          upcoming_shows.append(show.id)

      venue_details['num_upcoming_shows'] = len(upcoming_shows)
      venues.append(venue_details)

    # Add venue details to the location dict specified above  
    location_agg['venues'] = venues

    # Create final response object
    venue_list.append(location_agg)
    
  return render_template('pages/venues.html', areas=venue_list)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  venue_search = request.form.get('search_term')

  # Use search term to filter items by name
  search_count = db.session.query(Venue).filter(Venue.name.ilike(f'%{venue_search}%')).count()
  search_items = db.session.query(Venue).filter(Venue.name.ilike(f'%{venue_search}%')).all()

  search_list = []

  # Looop through the records found to create reponse object in the correct format
  for item in search_items:
    venue_details = {}
    venue_upcoming_shows = 0

    venue_shows = db.session.query(Show).with_entities(Show.venue_id, Show.start_time).filter_by(venue_id=item.id).all()

    # Loop through shows to confirm the correct upcoming shows
    for show in venue_shows:
      venue_show = {}

      if dateutil.parser.parse(str(show.start_time)).timestamp() > datetime.utcnow().timestamp():
        venue_upcoming_shows += 1
  

    venue_details.update({
      "id": item.id,
      "name": item.name,
      "num_upcoming_shows": venue_upcoming_shows
      })

    search_list.append(venue_details)

  response = {
    'count': search_count,
    'data': search_list
  }
 
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  # Query all records in the Venue table
  venues = db.session.query(Venue).with_entities(Venue.id, Venue.name, Venue.genres, Venue.city, Venue.state, Venue.phone, Venue.address, Venue.website_link, Venue.facebook_link, Venue.seeking_talent, Venue.seeking_description, Venue.image_link).all()
  
  venue_list = []

  # Loop through the venues to create the correct response format
  for venue in venues:
    
    venue_details = {}

    genres = venue.genres
    # Correct incorrect array for genre
    if isinstance(genres, list) and len(genres) > 1 and genres[0] == '{':
        genres = genres[1:-1]
        genres = ''.join(genres).split(",")

    venue_details.update({"id": venue.id,
    "name": venue.name,
    "genres": genres,
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link})

    past_shows = []
    upcoming_shows = []

    venue_shows = db.session.query(Show).with_entities(Show.artist_id, Show.start_time).filter_by(venue_id=venue.id).all()

    # Filter through all associated shows to group by past and upcoming
    for show in venue_shows:
      artist_show = {}

      artist = db.session.query(Venue).with_entities(Artist.name, Artist.image_link).filter_by(id=show.artist_id).limit(1).all()

      artist_show['artist_id'] = show.artist_id
      artist_show['artist_name'] = artist[0].name
      artist_show['artist_image_link'] = artist[0].image_link
      artist_show['start_time'] = str(show.start_time)

      if dateutil.parser.parse(str(show.start_time)).timestamp() < datetime.utcnow().timestamp():
        past_shows.append(artist_show)

      else:
        upcoming_shows.append(artist_show)
      

    venue_details.update({
        'past_shows': past_shows, 
        'upcoming_shows': upcoming_shows, 
        'past_shows_count':len(past_shows), 
        'upcoming_shows_count':len(upcoming_shows)
    })

    venue_list.append(venue_details)

  data = list(filter(lambda d: d['id'] == venue_id, venue_list))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  body={}

  try: 
      name = request.get_json()['name']
      city = request.get_json()['city']
      state = request.get_json()['state']
      address = request.get_json()['address']
      phone = request.get_json()['phone']
      genres = request.get_json()['genres']
      image_link = request.get_json()['image_link']
      website_link = request.get_json()['website_link']
      facebook_link = request.get_json()['facebook_link']
      seeking_talent =  request.get_json()['seeking_talent']
      seeking_description =  request.get_json()['seeking_description']

      if seeking_talent == 'y':
        seeking_talent = True
      else:
        seeking_talent = False

      venue = Venue(name=name,genres=genres,address=address, city=city, state=state, phone=phone,image_link=image_link,facebook_link=facebook_link, website_link=website_link, seeking_talent=seeking_talent,seeking_description=seeking_description)

      body['id'] = Venue.query.count() + 1
      body['name'] = venue.name
      body['city'] = venue.city
      body['state'] = venue.state

      db.session.add(venue)
      db.session.commit()
      
  # TODO: on unsuccessful db insert, flash an error instead.
  except:  
      error = True      
      db.session.rollback()
      print(sys.exc_info())

  finally:
      db.session.close()           
  if  error == True:
      flash('An error occurred. Venue ' + name + ' could not be listed.')
      abort(500)
  else:   
      flash('Venue ' + name + ' was successfully listed!') 
      return jsonify(body)
  
@app.route('/venues/<venue_id>/delete', methods=['GET', 'DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # Find the venue being viewed
  venue = db.session.query(Venue).get(venue_id)
  
  # Pass command to delete the record and commit the change
  db.session.delete(venue)
  db.session.commit()
  
  # Message user so the know the deletion went through
  flash(venue.name + ' and all associated shows were successfully deleted')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  artist_list = []
  artist_items = db.session.query(Artist).with_entities(Artist.id,Artist.name).all()
  
  # Loop through artists in the database
  for item in artist_items:
    artist_agg = {}

    # Build response dict with required artist details
    artist_agg['id'] = item.id
    artist_agg['name'] = item.name
    
    # Add items to arry to create final response object
    artist_list.append(artist_agg)

  return render_template('pages/artists.html', artists=artist_list)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  artist_search = request.form.get('search_term')

  # Use search term to filter items by name
  search_count = db.session.query(Artist).filter(Artist.name.ilike(f'%{artist_search}%')).count()
  search_items = db.session.query(Artist).filter(Artist.name.ilike(f'%{artist_search}%')).all()

  search_list = []

  # Looop through the records found to create reponse object in the correct format
  for item in search_items:
    artist_details = {}
    artist_upcoming_shows = 0

    artist_shows = db.session.query(Show).with_entities(Show.venue_id, Show.start_time).filter_by(artist_id=item.id).all()

    # Loop through shows to confirm the correct upcoming shows
    for show in artist_shows:

      if dateutil.parser.parse(str(show.start_time)).timestamp() > datetime.utcnow().timestamp():
        artist_upcoming_shows += 1
  

    artist_details.update({
      "id": item.id,
      "name": item.name,
      "num_upcoming_shows": artist_upcoming_shows
      })

    search_list.append(artist_details)

  response = {
    'count': search_count,
    'data': search_list
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist_result = []

  # Query all records in the Artist table
  artist_list = db.session.query(Artist).with_entities(Artist.id, Artist.name, Artist.genres, Artist.city, Artist.state, Artist.phone, Artist.website_link, Artist.facebook_link, Artist.seeking_venue, Artist.seeking_description, Artist.image_link).all()

  # Loop through the venues to create the correct response format
  for artist in artist_list:

    artist_details = {}

    genres = artist.genres
    # Correct incorrect array for genre
    if isinstance(genres, list) and len(genres) > 1 and genres[0] == '{':
        genres = genres[1:-1]
        genres = ''.join(genres).split(",")

    artist_details.update({"id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link})

    artist_past_shows = []
    artist_upcoming_shows = []

    artist_shows = db.session.query(Show).with_entities(Show.venue_id, Show.start_time).filter_by(artist_id=artist.id).all()

    # Filter through all associated shows to group by past and upcoming
    for show in artist_shows:
      venue_show = {}

      venue = db.session.query(Venue).with_entities(Venue.name, Venue.image_link).filter_by(id=show.venue_id).limit(1).all()

      venue_show['venue_id'] = show.venue_id
      venue_show['venue_name'] = venue[0].name
      venue_show['venue_image_link'] = venue[0].image_link
      venue_show['start_time'] = str(show.start_time)

      if dateutil.parser.parse(str(show.start_time)).timestamp() < datetime.utcnow().timestamp():
        artist_past_shows.append(venue_show)

      else:
        artist_upcoming_shows.append(venue_show)

    artist_details.update({
        'past_shows': artist_past_shows, 
        'upcoming_shows':artist_upcoming_shows, 
        'past_shows_count':len(artist_past_shows), 
        'upcoming_shows_count':len(artist_upcoming_shows)
    })

    artist_result.append(artist_details)
  
  data = list(filter(lambda d: d['id'] == artist_id, artist_result))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  # Get the correct artist details
  artist_details = db.session.query(Artist).with_entities(Artist.id, Artist.name, Artist.genres, Artist.city, Artist.state, Artist.phone, Artist.website_link, Artist.facebook_link, Artist.seeking_venue, Artist.seeking_description, Artist.image_link).filter_by(id=artist_id).limit(1).all()

  # Loop through the venue object and push fields into the appropriate form inputs
  for artist in artist_details:
    genres = artist.genres

    # Correct incorrect array for genre
    if isinstance(genres, list) and len(genres) > 1 and genres[0] == '{':
      genres = genres[1:-1]
      genres = ''.join(genres).split(",")

    artist_data = {'id': artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link}

    # TODO: populate form with fields from artist with ID <artist_id>
    form.name.data = artist.name
    form.genres.data = genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website_link.data = artist.website_link
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  # Find the correct record
  artist = db.session.query(Artist).get(artist_id)
  
  # Update fields based on the submitted form fields
  artist.name = request.form.get('name')
  artist.city = request.form.get('city')
  artist.state = request.form.get('state')
  artist.address = request.form.get('address')
  artist.phone = request.form.get('phone')
  artist.genres = request.form.getlist('genres')
  artist.facebook_link = request.form.get('facebook_link')
  artist.website_link = request.form.get('website_link')
  if request.form.get('seeking_venue')== 'y':
    artist.seeking_venue = True
  else:
    artist.seeking_venue = False
  
  artist.seeking_description =  request.form.get('seeking_description')
  artist.image_link = request.form.get('image_link')

  # Confirm the record edits
  db.session.commit()

  # Let the user know that the record was updated
  flash(artist.name +"'s page was sucessfully updated")

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # Get the correct venue details
  venue_details = db.session.query(Venue).with_entities(Venue.id, Venue.name, Artist.genres, Venue.city, Venue.state, Venue.address, Venue.phone, Venue.website_link, Venue.facebook_link, Venue.seeking_talent, Venue.seeking_description, Venue.image_link).filter_by(id=venue_id).limit(1).all()
  
  # Loop through the venue object and push fields into the appropriate form inputs
  for venue in venue_details:
    genres = venue.genres

    # Correct incorrect array for genre
    if isinstance(genres, list) and len(genres) > 1 and genres[0] == '{':
      genres = genres[1:-1]
      genres = ''.join(genres).split(",")

    venue_data = {'id': venue.id,
    "name": venue.name,
    "genres": genres,
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link}

    # TODO: populate form with fields from artist with ID <venue_id>
    form.name.data = venue.name
    form.genres.data = genres
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.website_link.data = venue.website_link
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  # Find the correct record
  venue = db.session.query(Venue).get(venue_id)
  
  # Update fields based on the submitted form fields
  venue.name = request.form.get('name')
  venue.city = request.form.get('city')
  venue.state = request.form.get('state')
  venue.address = request.form.get('address')
  venue.phone = request.form.get('phone')
  venue.genres = request.form.getlist('genres')
  venue.facebook_link = request.form.get('facebook_link')
  venue.website_link = request.form.get('website_link')
  if request.form.get('seeking_talent')== 'y':
    venue.seeking_talent = True
  else:
    venue.seeking_talent = False
  
  venue.seeking_description =  request.form.get('seeking_description')
  venue.image_link = request.form.get('image_link')

  # Confirm the record edits
  db.session.commit()

  # Let the user know that the record was updated
  flash(venue.name +"'s page was sucessfully updated")

  return redirect(url_for('show_venue', venue_id=venue.id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  body={}

  try: 
      name = request.get_json()['name']
      city = request.get_json()['city']
      state = request.get_json()['state']
      phone = request.get_json()['phone']
      genres = request.get_json()['genres']
      facebook_link = request.get_json()['facebook_link']
      website_link = request.get_json()['website_link']
      seeking_venue =  request.get_json()['seeking_venue']
      seeking_description =  request.get_json()['seeking_description']
      image_link = request.get_json()['image_link']

      if seeking_venue == 'y':
        seeking_venue = True
      else:
        seeking_venue = False

      artist = Artist(name=name,genres=genres, city=city, state=state, phone=phone,image_link=image_link,facebook_link=facebook_link, website_link=website_link, seeking_venue=seeking_venue,seeking_description=seeking_description)

      body['id'] = Artist.query.count() + 1
      body['name'] = artist.name
      body['city'] = artist.city
      body['state'] = artist.state

      db.session.add(artist)
      db.session.commit()

  # TODO: on unsuccessful db insert, flash an error instead.
  except:  
      error = True      
      db.session.rollback()
      print(sys.exc_info())

  finally:
      db.session.close() 

  if  error == True:
      flash('An error occurred. Artist ' + name + ' could not be listed.')
      abort(500)
  else:   
      flash('Artist ' + name + ' was successfully listed!') 
      return jsonify(body)

@app.route('/artists/<artist_id>/delete', methods=['GET', 'DELETE'])
def delete_artist(artist_id):

  # Find the venue being viewed
  artist = db.session.query(Artist).get(artist_id)
  
  # Pass command to delete the record and commit the change
  db.session.delete(artist)
  db.session.commit()
  
  # Message user so the know the deletion went through
  flash(artist.name + ' and all associated shows were successfully deleted')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []

  # Query for all shows in the database
  show_list = db.session.query(Show).with_entities(Show.id, Show.artist_id, Show.venue_id, Show.start_time).all()

  # Loop through the list andformat the show details for the reponse
  for show in show_list:
    temp_dict = {}

    venue_details = db.session.query(Venue).with_entities(Venue.name).filter_by(id=show.venue_id).limit(1).all()
    artist_details = db.session.query(Artist).with_entities(Artist.name, Artist.image_link).filter_by(id=show.artist_id).limit(1).all()

    temp_dict["venue_id"] = show.venue_id
    temp_dict["venue_name"] = venue_details[0].name
    temp_dict["artist_id"] = show.artist_id
    temp_dict["artist_name"] = artist_details[0].name
    temp_dict["artist_image_link"] = artist_details[0].image_link
    temp_dict["start_time"] = str(show.start_time)
  
    data.append(temp_dict)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  body={}

  try: 
      artist_id = request.get_json()['artist_id']
      venue_id = request.get_json()['venue_id']
      start_time = request.get_json()['start_time']

      show = Show( start_time=start_time, artist_id=artist_id,venue_id=venue_id)

      body['id'] = Show.query.count() + 1
      body['artist_id'] = show.artist_id
      body['venue_id'] = show.venue_id
      body['start_time'] = show.start_time

      artist_name = db.session.query(Artist).with_entities(Artist.name).filter_by(id=show.artist_id).all()

      db.session.add(show)
      db.session.commit()
      # on successful db insert, flash success
      # flash('Show on ' + start_time + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except:  
      error = True      
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close() 

  if  error == True:
      flash('An error occurred. Show for '+ artist_name[0].name + ' at ' + start_time + ' could not be listed.')
      abort(500)
  else:   
      flash('Show '+ artist_name[0].name  + ' at ' + start_time + ' was successfully listed!') 
      return jsonify(body)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:

if __name__ == '__main__':
    app.run(debug=True)


# Or specify port manually:

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)

