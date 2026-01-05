******PREPARATION******
- Put original test sequences in the ```test_sequences``` directory
- *If AV1 encoded videos exist*: Put encoded videos in the ```av1_sequences```  directory
- *Else*: run the Python script ```encoding.py``` --> this will put the videos already in the correct directory

******SETUP NGINX******
- Go to https://nginx.org/en/download.html and select appropriate mainline version (*macOS might need installation via Homebrew?*)
- For (*Windows 10*) choose ```nginx/Windows-1.29.4 (mainline)```
- Put the encoded videos in ```<path_to_nginx>/html/videos/```
- In ```<path_to_nginx>/conf/nginx.conf``` change the port in the 'listen' directive from 80 to 8123
	--> example 
	```
 	server {
    		listen       80; //change this to 8123
    		server_name  localhost;
   		...
	}
 	```

***INDEX.HTML FILE***
- If you want to edit the default HTML file on port 8123:
--> ***edit this***: ```<path_to_nginx>/html/index.html```
- This file will provide the video player

***Start NGINX server (Powershell)***:
	```start nginx```

***Stop NGINX server (Powershell)***:
	```.\nginx -s stop```

***Reload NGINX server (Powershell)***:
	```.\nginx -s reload``` (server must be running beforehand; use ****after every change*** on the server (config, content, etc.)*


******WHY .\nginx SOMETIMES, OTHERWISE NOT?******
- ```-s signal```     : send signal to a master process: stop, quit, reopen, reload
--> No signal to send without process being started first
