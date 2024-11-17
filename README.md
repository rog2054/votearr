# votearr

## ❓ Purpose

**tldr : Vote to delete old media from your Radarr library**

This utility gives a simple user-friendly way for multiple viewers of a Radarr library (eg a household) to each cast a vote about if the media should be kept for re-watching, or deleted forever. They also have the option to skip a vote for example if they haven't yet watched it or are currently undecided.

It is provided as a ready-to-build docker image 🐳 and can be run on either Windows or Linux.

Once installed your group use it via a simple web interface on a Computer or Mobile device.

***

## 🚀 Quick Install

### Start in 3 steps ###
1. Clone this repo
2. Edit [settings.ini](#configuration)
3. Build and run the docker image.

*See below for [detailed install instructions](#detailedinstallsteps) for Windows or Linux*

***
<a id="configuration"></a>
## 📜 Configuration

### settings.ini parameters
👀 This file contains configuration specific to your installation and must be edited before first use 👀

There are 4 settings to configure. The settings.ini file provided contains examples and comments.

##### radarr_url
The local ip and port for your existing Radarr installation.

example: `radarr_url=http://192.168.1.24:7878`
 
##### radarr_apikey
The API key for your existing Radarr.

You can find this within Radarr under the Settings - General tab

example: `radarr_apikey=6c4d96beda244f755427b34f632b4227`

##### voting_users

Users who will be able to vote. The order isn't important, however it must be a comma-separated list of names (with or without a space after the comma).

example: `voting_users = Bob,Alice,Carlos`

valid alternative: `voting_users = Bob, Alice, Carlos`

##### delete_votes_required
The minimum number of unique users voting 'Delete' for an item before it will be considered for permanent deletion from the Radarr library. It is suggested to set this to the number of users (ie 3 for a 3-person household) so items can only be deleted once nobody wants them anymore.

example: `delete_votes_required=3`

***
<a id="detailedinstallsteps"></a>
## 💡 Detailed Install Instructions

### Setup in Windows

1. Clone this repo into a folder, eg c:\votearr
2. Edit the settings.ini file - see [Configuration - settings.ini](#configuration) for guidance
3. If you do not have Docker already download, install, and run [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows
4. Identify your machine IP address `ipconfig`
5. From the command prompt, build and run the docker image

     c:\votearr> `docker-compose up -build `
6. Once you are happy it is working, exit this instance with <kbd>Ctrl</kbd>+<kbd>c</kbd> then relaunch as a background container `docker-compose up -d`


### Setup in Linux
(based on a fresh minimal server install of Ubuntu, but any similar distro should be a similar process)

1. Clone this repo into a folder, eg /home/user/votearr
2. Edit the settings.ini file - see [Configuration - settings.ini](#configuration) for guidance
3. Install Docker Compose
`sudo apt-get install docker-compose`
 
   Add the current linux user to the docker group `sudo usermod -aG docker ${USER}`

   Logoff then logon again for the new group membership to apply
4. Identify your machine IP address `ip a`
5. Build and run the docker image `docker-compose up --build`
6. Once you are happy it is working, exit this instance with <kbd>Ctrl</kbd>+<kbd>c</kbd> then relaunch as a background container `docker-compose up -d`

***

## 👪 User Guide

### The votearr web interface

`http://192.168.1.24` 

From a web browser go to http://ipaddress from step 4 above, eg 

*For simplicity the ip address 192.168.1.24 will be used throughout the remainder of this Readme but remember to replace it with your own ip*

The first page a user reaches is the Select User page. 

Click on your name to proceed to media voting.

![screenshot](/screenshots/select_user.png)

### Media Voting

After the user has been selected, the media voting page will load. 
 
This page shows the Title of the media, an image of the media (if available), and the 3 voting buttons
Media items are shown in a random order (rather than alphabetically for example) to keep things interesting.

![screenshot](/screenshots/vote_buttons.png)

Any items a user votes as *Decide Later* will be skipped from future voting shown to them *until* they have voted on all other unvoted media items. When they have voted on every unvoted item available, these Decide Later voted items will then become available again to be randomly re-presented again so a Keep/Remove vote may be cast. A user is free to select to Decide Later again, of course.

At any point the user may close the page and return at another time. 

Votes are saved immediately to the database upon each vote. Voting will resume with a newly randomly presented media item on their next visit to the Votearr url. 

### Viewing voting status

`http://192.168.1.24/list`

Anyone can view a table of the current votes by going to this page 

Above the table there is a simple bar chart showing how much of the library each user has voted so far.

![screenshot](/screenshots/vote_results_summary.png)
Here notice the last item in this example has received Delete votes from all users, so will be a candidate for actual deletion 

### Deleting voted items from your library

`http://192.168.1.24/ready_to_delete`

Media items that everyone voted to delete are shown on a page along with a **Delete Now** button.

![screenshot](/screenshots/delete_after_vote_consensus.png)

Pressing that button next to each item on this page will delete that media from Radarr (and delete the media file from your media storage).

***

## Future Improvements
This is a quick project I threw together for my own use. I am not a professional developer and certainly not a front-end designer either, I am the ideas person.

I may implement some of these improvements at some point however others are welcome to collaborate and contribute updates in the spirit of open source code.

With that said here are some future improvements I can think of. These are listed in no particular order.

- [ ] User Authentication - not a high priority for me for a LAN-only project such as this.
- [ ] A way for a user to edit/change their vote
- [ ] Periodically (maybe via a new url triggered from a cron job) remove all 'Keep' votes from the database, eg every 3 or 6 months. This would stop items ending up Keep forever and the resulting bloated media library. A better variation of this might be 'x months after that user last voted on that item' which would mean adding a vote timestamp to the voting db of course (not complex really).
- [ ] A better nicer-looking GUI - no explanation needed, the current one is functional and 'not bad' but absolutely it is far from great!
- [ ] A menu navbar for the GUI - another non-essential item hence not created initially, but would add a bit more glamour to this tool
- [ ] Removal of orphan votes from the db (ie when the associated media no longer exists in Radarr). This could be done as part of the 'ready_to_delete' deletion function, however ideally would also detect and tidy if the media was deleted separately outside of Votearr.
- [ ] Caching of the media posters - another one that doesn't seem that important to me for a low-usage system such as this, with 3 people voting you are downloading the image 3 times, big deal. However in the interests of optimum efficiency these could be saved and stored locally on the first vote, and then retrieved locally for the 2nd and 3rd person to vote on them. (I couldn't find a way to load the image directly from the Radarr Server without the end-user logging into Radarr before they vote in Votearr, which defeats the point of using the API)


## 🙏 Acknowledgements

| | |
| :------------- |:-------------| 
| [**Radarr**](https://radarr.video/)     | An excellent media manager for videos | 
| [**arrapi**](https://github.com/Kometa-Team/ArrAPI) | Library of python bindings for Radarr and Sonarr |
| [**Flask**](https://flask.palletsprojects.com/en/stable/) | Flask is a lightweight WSGI web application framework |
| [**SQLite**](https://www.sqlite.org/) | A small, fast, self-contained, high-reliability, full-featured, SQL database engine |
| [**Python**](https://www.python.org/) | A popular programming language suitable for a wide range of abilities and use cases|
| [**Docker**](https://www.docker.com/) | An easy way to package code for use on different systems without dependency issues

***

## 💀 Privacy

- The only data saved by votearr is saved into the .db file which is stored locally on your docker host machine (outside of the docker container)
- This .db file contains votes, however does not show the media names or public references (such as imdb/tmdb ID's) - it only stores the Radarr media ID for it. These values are specific to your individual Radarr environment. In other words, if anyone obtains this .db file cannot determine what media you have in your library unless they also have access to *your* Radarr.

***
