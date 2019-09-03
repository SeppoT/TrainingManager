"use strict";

const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

const USERS_URL = "http://localhost:5000/api/users/"

function renderError(error) {
   
    $("#notificationarea").append("<p class='error'>" + error.status +" "+ error.statusText + "</p>");
}

function renderMsg(msg) {
    $("#notificationarea").append("<p>" + msg + "</p>");
    $("#notificationarea").animate({ scrollTop: $('#notificationarea').prop("scrollHeight")}, 100);
}

function getResource(href, renderer) {
    $.ajax({
        url: href,
        success: renderer,
        error: renderError
    });
}

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


function userAdded(data, status, jqxhr)
{
	let href = jqxhr.getResponseHeader("Location");
	renderMsg("User added : "+href)
	loadUserList()
}

function loadUserList()
{
	sendData("http://localhost:5000/api/users/", "GET", {}, usersLoaded);
}

function usersLoaded(data, status, jqxhr)
{
	$("#usertablebody").empty();
	//console.log(data.items)
	for (let [key, value] of Object.entries(data.items)) {
    	//console.log(key, value);
    	$("#usertablebody").append("<tr><td>"+value.firstname+"</td><td>"+value.lastname+"</td><td>"+value["@controls"]["self"]["href"]+"</td>");
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

   $('#createUsers').on('click', function(event) 
	{
		console.log("Create test users");
		renderMsg("Creating test users...")
		
		let data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":true};
		sendData(USERS_URL, "POST", data, userAdded);

		data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":false};
		sendData(USERS_URL, "POST", data, userAdded);
		data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":false};
		sendData(USERS_URL, "POST", data, userAdded);
		data = {"firstname":"testuser"+Math.floor((Math.random() * 10000) + 1),"lastname":"testuser"+Math.floor((Math.random() * 10000) + 1),"isAdmin":false};
		sendData(USERS_URL, "POST", data, userAdded);

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

	loadUserList()
});

