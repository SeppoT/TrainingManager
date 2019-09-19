"use strict";

const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

//these could be read from /api/ root control
const USERS_URL = "http://localhost:5000/api/users/"
const COURSES_URL = "http://localhost:5000/api/trainingcourses/"

function renderError(error) {
    $("#notificationarea").append("<p class='error'>" + error.status +" "+ error.statusText + "</p>");
}

function renderMsg(msg) {
    $("#notificationarea").append("<p>" + msg + "</p>");
    $("#notificationarea").animate({ scrollTop: $('#notificationarea').prop("scrollHeight")}, 100);
}

//load resource with ajax, based on course example
function getResource(href, renderer) {
    $.ajax({
        url: href,
        success: renderer,
        error: renderError
    });
}

//follow link, based on course example
function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer);
}

//send ajax request to server, process response with given postprocessor , based on course example
function sendData(href, method, item, postProcessor) {
    $.ajax({
        url: href,
        type: method,
        data: JSON.stringify(item),
        contentType: PLAINJSON,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}

//render user view ( course list )
function renderUser(body) {
	renderMsg(JSON.stringify(body));
	$("#userview").empty()
	$("#userview").show()	
	$("#usertable").hide()
	$(".usertablenav").hide()
	$(".usernav").show()
	$("#coursetable").show()
	$(".coursenav").hide()
	$("#courseview").hide()

	loadCourseList()

	$('#backtouserlistbutton').off('click');
	$('#backtouserlistbutton').on('click', function(event) 
	{
		//back , could be read from control
		 renderUserList()
	})

	$('#deleteuserbutton').off('click');
	$('#deleteuserbutton').on('click', function(event) 
	{
		 let data = {}
		 renderMsg("User delete:"+body["@controls"]["trainingmanager:delete-user"]["href"]);
		 sendData(body["@controls"]["trainingmanager:delete-user"]["href"], "DELETE", data, userDeleted);
	})

	$("#userview").append("<h3>"+body.firstname+" "+body.lastname+"</h3>")
}

//render course view 
function renderCourse(body) {
	renderMsg(JSON.stringify(body));
	$("#courseview").empty()
	$("#userview").hide()	
	$("#usertable").hide()
	$(".usertablenav").hide()
	$(".usernav").hide()
	$("#coursetable").hide()
	$(".coursenav").show()
	$("#courseview").show()

	$('#backtouserlistbutton2').off('click');
	$('#backtouserlistbutton2').on('click', function(event) 
	{
		 renderUserList()
	})
	//$("#courseview").append("<h5>"+JSON.stringify(body)+"</h5>")
	
	let htmlObject = document.createElement('div');
	htmlObject.innerHTML=body.coursedatajson;
	$("#courseview").append(htmlObject);	
	for (let [key, value] of Object.entries(body.medialist)) {

		$("#courseview").append("<img class='courseimagethumb' src='"+value.url+"'></img>")
	}
}

function userDeleted(data, status, jqxhr)
{	
	renderMsg("User deleted")
	loadUserList();
	renderUserList();
}

function renderUserList() {
	//collection api url not from controls, fixed url
	$("#userview").hide()	
	$("#usertable").show()
	$(".usertablenav").show()
	$(".usernav").hide()
	$("#coursetable").hide()
	$(".coursenav").hide()
	$("#courseview").hide()


}

function userAdded(data, status, jqxhr)
{
	let href = jqxhr.getResponseHeader("Location");
	renderMsg("User added : "+href)
	loadUserList()
}

function courseAdded(data, status, jqxhr)
{
	let href = jqxhr.getResponseHeader("Location");
	renderMsg("Course added : "+href+" id:"+data)
	addTestMediasToCourse(data);
	loadCourseList()
}

//add some test images to course with the api
function addTestMediasToCourse(courseid)
{
	let MEDIA_URL = "/api/trainingcourses/"+courseid+"/medias/";
	let data = {"url":"https://cdn.pixabay.com/photo/2019/08/15/23/55/light-bulb-4409116_960_720.jpg","type":"image"}
	sendData(MEDIA_URL, "POST", data, mediaAdded);
	data = {"url":"https://cdn.pixabay.com/photo/2019/08/30/18/43/mountains-4441978_960_720.jpg","type":"image"}
	sendData(MEDIA_URL, "POST", data, mediaAdded);
	data = {"url":"https://cdn.pixabay.com/photo/2013/11/28/10/36/road-220058_960_720.jpg","type":"image"}
	sendData(MEDIA_URL, "POST", data, mediaAdded);
	//https://cdn.pixabay.com/photo/2019/08/30/18/43/mountains-4441978_960_720.jpg
	//https://cdn.pixabay.com/photo/2019/08/15/23/55/light-bulb-4409116_960_720.jpg
	//https://cdn.pixabay.com/photo/2013/11/28/10/36/road-220058_960_720.jpg
}

function mediaAdded(data, status, jqxhr)
{
	let href = jqxhr.getResponseHeader("Location");
	renderMsg("Media added : "+href)	
}

function loadUserList()
{
	sendData("http://localhost:5000/api/users/", "GET", {}, usersLoaded);
}

function loadCourseList()
{
	sendData("http://localhost:5000/api/trainingcourses/", "GET", {}, coursesLoaded);
}

function usersLoaded(data, status, jqxhr)
{
	$("#usertablebody").empty();
	//console.log(data.items)
	for (let [key, value] of Object.entries(data.items)) {
    	//console.log(key, value);
    	$("#usertablebody").append("<tr><td>"+value.firstname+"</td><td>"+value.lastname+"</td><td><a class='btn btn-primary' type='button' href='"+value["@controls"]["self"]["href"]+"' onClick='followLink(event, this, renderUser)'>Select user</a></td>");
	}
}

function coursesLoaded(data, status, jqxhr)
{
	$("#coursetablebody").empty();
	//console.log(data.items)
	for (let [key, value] of Object.entries(data.items)) {
    	//console.log(key, value);
    	$("#coursetablebody").append("<tr><td>"+value.name+"</td><td><a class='btn btn-primary' type='button' href='"+value["@controls"]["self"]["href"]+"' onClick='followLink(event, this, renderCourse)'>Open course</a></td>");
	}
}

function dataDeleted(data, status, jqxhr)
{
	renderMsg("Database content deleted");
	loadUserList()
}


$(document).ready(function () {
   //getResource("http://localhost:5000/api/sensors/", renderSensors);
   $('#clearButton').on('click', function(event) 
	{
		console.log("Cleared notification area");
		$("#notificationarea").empty();
	})
   //create test data (users and courses)
   $('#createData').on('click', function(event) 
	{
		console.log("Create test data");
		renderMsg("Creating test users...")		
		let data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":true};
		sendData(USERS_URL, "POST", data, userAdded);
		data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":false};
		sendData(USERS_URL, "POST", data, userAdded);
		data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":false};
		sendData(USERS_URL, "POST", data, userAdded);
		data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":false};
		sendData(USERS_URL, "POST", data, userAdded);

		data = {"name":"Test course "+Math.floor((Math.random() * 10000) + 1)};
		data["coursedatajson"]="<p><h5>This is example course introduction title</h5></p><p>Real course or other training would be introduced here.</p>";
		sendData(COURSES_URL, "POST", data, courseAdded);
	})

	$('#deleteData').on('click', function(event) 
	{
		console.log("Delete data");
		renderMsg("Deleting data...")
		let data = {}
		sendData("http://localhost:5000/trainingmanager/truncate/", "GET", data, dataDeleted);
	})

	$('#refresh').on('click', function(event) 
	{
		console.log("Refresh data from server");
		renderMsg("Refresh data from server...")
		loadUserList()
	})
	$("#userview").hide();
	$(".usernav").hide();

	loadUserList();
});

