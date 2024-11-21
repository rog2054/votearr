from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from arrapi import RadarrAPI, ArrException, NotFound
import random
import configparser
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/votes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load settings.ini values
config = configparser.ConfigParser()
config.read('settings.ini')
radarr_url = config['DEFAULT']['radarr_url']
radarr_apikey = config['DEFAULT']['radarr_apikey']
delete_votes_required = int(config['DEFAULT']['delete_votes_required'])
voting_users = re.split(r',\s*', config['DEFAULT']['voting_users'])

# Initialize Radarr API client
radarr = RadarrAPI(radarr_url, radarr_apikey)

# Define the Vote model
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(80), nullable=False)
    vote = db.Column(db.String(80), nullable=False)

db.create_all()

# Helper function to get a random media item that the user has not voted on
def get_random_media(user):
    # Get all media items from Radarr
    media_items = radarr.all_movies()  # Returns a list of Movie objects

    # Filter out media items that the user has already voted on or that do not have a file
    voted_media_ids = [vote.media_id for vote in Vote.query.filter_by(user=user).all()]
    unvoted_media_items = [
        item for item in media_items if item.id not in voted_media_ids and item.hasFile
    ]

    if not unvoted_media_items:
        # if there are no items which haven't been voted on, return the set of items which the user selected as Undecided, so they can reconsider these
        decidelater_media_ids = [vote.media_id for vote in Vote.query.filter_by(user=user, vote='Decide later').all()]
        decidelater_media_items = [
        item for item in media_items if item.id in decidelater_media_ids and item.hasFile
        ]
        if not decidelater_media_items:
            # There really is nothing left to vote on
            return None
        else:
            unvoted_media_items = decidelater_media_items

    # Choose a random unvoted media item
    random_item = random.choice(unvoted_media_items)
    print(f"random_item: {random_item}")
    print(f"random_item.images: {random_item.images}")

    # Extract the first image URL from the images list
    poster_url = random_item.images[0].remoteUrl if random_item.images else None

    return {
        "id": random_item.id,
        "title": random_item.title,
        "poster_url": poster_url  # Use the first image URL as the poster
    }

def purge_votes_for_nomediafound_item(media_id):
    mediavotes = Vote.query.filter_by(media_id=media_id).count()
    if mediavotes == 0:
        # no votes for this media_id, no purge needed
        return
    
    else:    
        media_items = radarr.all_movies()
        librarysize = len(media_items)
        if librarysize < 10:
            # exit without purge if fewer than 10 media items found - possible connectivity problem between votearr and radarr
            return
        else:
            votes_to_delete = Vote.query.filter_by(media_id=media_id)
            purged_votes = votes_to_delete.delete()
            db.session.commit()
            print (f"{purged_votes} votes purged from Vote db")
            return

def calc_user_voted_percent(user):
    uservotes = Vote.query.filter_by(user=user).count()
    
    media_items = radarr.all_movies()  # Returns a list of Movie objects

    # Filter out media items that the user has already voted on or that do not have a file
    media_items_withfiles = [
        item for item in media_items if item.hasFile
    ]
    count_media_items_withfiles = len(media_items_withfiles)
    userpercentvoted = round(uservotes/count_media_items_withfiles*100)
    if userpercentvoted > 100:
        # fudge to prevent showing values over 100%, which happens if voted items have since been deleted from the library
        userpercentvoted = 100
    return userpercentvoted

def calc_user_voted_percents(user):
    # zero initial values so we don't return null
    uservotes_keep = 0
    uservotes_delete = 0
    uservotes_decidelater = 0
    
    uservotes_keep = Vote.query.filter_by(user=user, vote='Keep').count()
    uservotes_delete = Vote.query.filter_by(user=user, vote='Remove').count()
    uservotes_decidelater = Vote.query.filter_by(user=user, vote='Decide later').count()
    
    media_items = radarr.all_movies()  # Returns a list of Movie objects

    # Filter out media items that the user has already voted on or that do not have a file
    media_items_withfiles = [
        item for item in media_items if item.hasFile
    ]
    count_media_items_withfiles = len(media_items_withfiles)
    if count_media_items_withfiles == 0:
        # return safe values from this function if no media items found in Radarr
        return 0,0,0
    
    userpercentvoted_keep = round(uservotes_keep/count_media_items_withfiles*100)
    userpercentvoted_delete = round(uservotes_delete/count_media_items_withfiles*100)
    userpercentvoted_decidelater = round(uservotes_decidelater/count_media_items_withfiles*100)
    userpercent_unvoted = 100 - userpercentvoted_keep - userpercentvoted_delete - userpercentvoted_decidelater
    
    # fudges to prevent showing values over 100%, which happens if voted items have since been deleted from the library
    if userpercentvoted_keep > 100:
        userpercentvoted_keep = 100
    
    if userpercentvoted_delete > 100:
        userpercentvoted_delete = 100
        
    if userpercentvoted_decidelater > 100:
        userpercentvoted_decidelater = 100
        
    # return user percentage voted for keep, delete, decide later, and unvoted
    return userpercentvoted_keep,userpercentvoted_delete,userpercentvoted_decidelater, userpercent_unvoted

# Route to select a user
@app.route('/')
def index():
    return render_template('index.html', users=voting_users)

@app.route('/vote/<user>', methods=['GET', 'POST'])
def vote(user):
    if request.method == 'POST':
        media_id = request.form['media_id']
        vote_value = request.form['vote']

        # Check if there is already a vote for this user and media item
        existing_vote = Vote.query.filter_by(media_id=media_id, user=user).first()

        if existing_vote:
            # Update the existing vote
            existing_vote.vote = vote_value
        else:
            # Create a new vote if no existing vote is found
            new_vote = Vote(media_id=media_id, user=user, vote=vote_value)
            db.session.add(new_vote)

        # Commit the changes to the database
        db.session.commit()

        # Redirect to a new media item
        return redirect(url_for('vote', user=user))

    # Get a random media item for the user to vote on
    media_item = get_random_media(user)
    if not media_item:
        return redirect(url_for('ready_to_delete'))

    return render_template(
        'vote.html',
        user=user,
        userpercentvoted = calc_user_voted_percent(user),
        media_name=media_item["title"],
        media_id=media_item["id"],
        poster_url=media_item["poster_url"]
    )

@app.route('/list')
def list_view():
    # Aggregate votes by media and collect a list of unique users
    media_votes = {}
    user_list = set()

    # Query all votes from the database
    all_votes = Vote.query.all()

    # Populate the media_votes and user_list
    for vote in all_votes:
        if vote.media_id not in media_votes:
            media_votes[vote.media_id] = {user: None for user in user_list}
        media_votes[vote.media_id][vote.user] = vote.vote
        user_list.add(vote.user)

    # Convert user_list to a sorted list
    user_list = sorted(user_list)

    userstats = []
    for thisuser in user_list:
        userpercentvoted_keep, userpercentvoted_delete, userpercentvoted_decidelater, userpercentvoted_unvoted = calc_user_voted_percents(thisuser)
        userstats.append({"user":thisuser,"keep":userpercentvoted_keep,"delete":userpercentvoted_delete,"decidelater":userpercentvoted_decidelater,"unvoted":userpercentvoted_unvoted})
        
    # Fetch media details from Radarr for each media_id in media_votes
    media_details = []
    for media_id in media_votes.keys():
        try:
            media_item = radarr.get_movie(media_id)
            media_details.append({
                "id": media_id,
                "title": media_item.title,
                "year": media_item.year,
                "votes": media_votes[media_id]
            })
        except Exception as e:
            print(f"Error fetching media item {media_id}: {e}")
            # media no longer exists, so purge any related votes
            purge_votes_for_nomediafound_item(media_id)

    # sort alphabetically by title
    media_details.sort(key=lambda x: x['title'])

    # Pass the media_details and user_list to the template
    return render_template('list.html', media_list=media_details, user_list=user_list, userstats=userstats)

@app.route('/delete/media_id/<media_id>')
def delete_now(media_id):
    media_id = int(media_id)
    
    # safety check if we have 'delete_votes_required' delete votes for this movie id
    this_media_votes = Vote.query.filter_by(media_id=media_id, vote='Remove').count()
    if this_media_votes >= delete_votes_required:    
        # call arrapi to delete this movie id
        try:
            output = radarr.delete_movie(media_id)
        except (ArrException, NotFound):
            movie_deleted = "Error movie not found"
            return render_template('delete_status.html', movie_deleted=movie_deleted)
            
        # return: display outcome success/fail, including the deleted movie_id.name
        if output:
            movie_deleted = f"{output.title} deleted successfully"
        else:
            movie_deleted = "Error deleting movie"
    else:
        this_movie = radarr.get_movie(media_id)
        movie_deleted = f"Unable to delete {this_movie.title}, need {delete_votes_required} votes only have {this_media_votes}" 
    return render_template('delete_status.html', movie_deleted=movie_deleted)        
        
# Route to view media items that are ready to be requested (manually) for actual library removal
@app.route('/ready_to_delete')
def ready_to_delete():
    # Find all media items with votes
    media_votes = {}
    for vote in Vote.query.all():
        if vote.media_id not in media_votes:
            media_votes[vote.media_id] = {"keep": 0, "remove": 0, "decide later": 0}
        media_votes[vote.media_id][vote.vote.lower()] += 1

    # Find which of these media items has met the 'delete_votes_required' for "remove" votes
    to_delete = []
    for media_id, votes in media_votes.items():
        if votes["remove"] >= delete_votes_required:
            try:
                media_item = radarr.get_movie(media_id)
                to_delete.append({
                    "title": media_item.title,
                    "year": media_item.year,
                    "delete_url": "/delete/media_id/"+str(media_id)
                })
            except (ArrException, NotFound):
                # movie not found - means it has already been deleted, no need to panic!
                continue
    return render_template('ready_to_delete.html', to_delete=to_delete)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
