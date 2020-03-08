


## Introduction


## Event Format

The event body adheres to the standard CloudWatch event format, and describes all properties of the channel and the specific item in the channel. All properties correspond to the RSS 2.0 specification found [here]([https://cyber.harvard.edu/rss/rss.html](https://cyber.harvard.edu/rss/rss.html)). 

 - **source** *(string)* - The URL used to derive to content of the RSS feed
 - **detail** *(object)* 
	 - **channel** *(object)* - Holds all properties of the channel
		 - **title** *(string)* - The name of the channel
		 - **link** *(string)* - The URL to the HTML website corresponding to the channel
		 - **description** *(string)* - Phrase or sentence describing the channel 
		 - **categories** *(array&lt;string&gt;)* - An array of categories that the channel belongs to
		 - **language** *(string)* - The language the channel is written in
		 - **copyright** *(string)* - Copyright notice for content in the channel
		 - **managingEditor** *(string)* - Email address for person responsible for editorial content
		 - **webMaster** *(string)* - Email address for person responsible for technical issues relating to channel
		 - **pubDate** *(string)* - The publication date for the content in the channel
		 - **lastBuildDate** *(string)* - The last time the content of the channel changed
		 - **generator** *(string)* - A string indicating the program used to generate the channel
		 - **docs** *(string)* - A URL that points to the documentation for the format used in the RSS file
		 - **cloud** *(object)* - Allows processes to register with a cloud to be notified of updates to the channel, implementing a lightweight publish-subscribe protocol for RSS feeds
		 - **ttl** *(number)* - Number of minutes that indicates how long a channel can be cached before refreshing from the source
		 - **image** *(object)* - Specifies a GIF, JPEG or PNG image that can be displayed with the channel
			 - **url** *(string)* - The URL of a GIF, JPEG or PNG image that represents the channel
			 - **title** *(string)* - Describes the image, it's used in the ALT attribute of the HTML &lt;img&gt; tag when the channel is rendered in HTML
			 - **link** *(string)* -The URL of the site, when the channel is rendered, the image is a link to the site
			 - **width** *(number)* - Width of the image
			 - **height** *(number)* - Height of the image
		- **rating** *(string)* - The [PICS](http://www.w3.org/PICS/) rating for the channel
		- **textInput** *(object)* - Specifies a text input box that can be displayed with the channel
			- **title** *(string)* - The label of the Submit button in the text input area
			- **description** *(string)* - Explains the text input area
			- **name** *(string)* - The name of the text object in the text input area
			- **link** *(string)* - The URL of the CGI script that processes text input request
		- **skipHours** *(array&lt;number&gt;)* - A hint for aggregators telling them which hours they can skip, which takes the form of an array that contains up to 24 numbers, between 0 and 23, that specify a time in GMT 
		- **skipDays** *(array&lt;string&gt;)*- A hint for aggregators telling them which days they can skip, which takes the form of an array that contains up to seven strings, with possible values of:
			- *Monday*
			- *Tuesday*
			- *Wednesday*
			- *Thursday*
			- *Friday*
			- *Saturday*
			- *Sunday*
	 - **item** *(object)*- Holds all properties of an item in the channel
		 - **title** *(string)* - The title of the item
		 - **link** *(string)* - The URL of the item
		 - **description** *(string)* - The item synopsis
		 - **author** *(string)* - Email address of the author of the item
		 - **categories** *(array&lt;string&gt;)* - An array of categories that the item belongs to
		 - **comments** *(string)* - URL of a page for comments relating to the item
		 - **enclosure** *(object)* - Describes a media object that is attached to the item
			 - **url** *(string)* - Where the enclosure is located
			 - **length** *(number)* - How big the media object is
			 - **type** *(string)* - The MIME type of the media object
		 - **guid** *(string)* - A string that uniquely identifies the item
		 - **pubDate** *(string)* - Indicates when the item was published
		 - **source** *(string)* - The RSS channel that the item came from

  

*Example*:

   ```json
   { 
	   "version":  "0", 
	   "id":  "00000000-0000-0000-0000-000000000000", 
	   "detail-type":  "New RSS Item", 
	   "source":  "https://www.nasa.gov/rss/dyn/breaking_news.rss", 
	   "account":  "123456789012", 
	   "time":  "2020-03-07T06:08:01Z", 
	   "region":  "us-east-1", 
	   "resources": [], 
	   "detail": { 
		   "item": { 
			   "title":  "SpaceX Dragon Heads to Space Station with NASA Science, Cargo", 
			   "link":  "http://www.nasa.gov/press-release/spacex-dragon-heads-to-space-station-with-nasa-science-cargo-1", 
			   "description":  "A SpaceX Dragon cargo spacecraft is on its way to the International Space Station after launching at 11:50 p.m. EST Friday. Dragon will deliver more than 4,300 pounds of NASA cargo and science investigations, including a new science facility scheduled to be installed to the outside of the station during a spacewalk this spring.", 
			   "enclosure": { 
				   "url":  "http://www.nasa.gov/sites/default/files/styles/1x1_cardfeed/public/thumbnails/image/spx_launch_0.png?itok=jlsrAtrt", 
				   "length":  "953717", 
				   "type":  "image/png"
			  }, 
			  "guid":  "http://www.nasa.gov/press-release/spacex-dragon-heads-to-space-station-with-nasa-science-cargo-1", 
			  "pubDate":  "Fri, 06 Mar 2020 23:59 EST", 
			  "source": { 
				  "url":  "http://www.nasa.gov/rss/dyn/breaking_news.rss", 
				  "name":  "NASA Breaking News" 
			  } 
		  }, 
		  "channel": { 
			  "title":  "NASA Breaking News", 
			  "description":  "A RSS news feed containing the latest NASA news articles and press releases.", 
			  "link":  "http://www.nasa.gov/", 
			  "language":  "en-us", 
			  "managingEditor":  "jim.wilson@nasa.gov", 
			  "webMaster":  "brian.dunbar@nasa.gov", 
			  "docs":  "http://blogs.harvard.edu/tech/rss" 
		 } 
	  } 
	}