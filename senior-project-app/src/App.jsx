import { useEffect, useState } from "react";
// import { BrowserRouter, Link, Switch, Route } from 'react-router-dom';
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";

// import axios from "axios";

// import React, { useState } from 'react';

function App() {
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);
  const [linkedInUrls, setLinkedInUrls] = useState(""); // New state variable for LinkedIn URLs
  const [linkedInResults, setLinkedInResults] = useState([]); // Add this line

  const handleImageUpload = (event) => {
    setImage(event.target.files[0]);
  };

  const handleLinkedInUrlsChange = (event) => { // New handler for LinkedIn URLs input field
    setLinkedInUrls(event.target.value);
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const formData = new FormData();
    formData.append("image", image);

    fetch(`${import.meta.env.VITE_APP_SERVER_URL}/detect_faces`, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json(); // Add this line
      })
      .then((data) => {
        setResults(data); // Add this line
        console.log(data); // Add this line
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  };

  const handleLinkedInSubmit = (event) => { // New handler for LinkedIn URLs submit button
    event.preventDefault();

    fetch(`${import.meta.env.VITE_APP_SERVER_URL}/submit_urls`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ urls: linkedInUrls.split('\n') }), // Split the URLs by newline and send them as an array
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log(data);
        setLinkedInResults(data); // Set the LinkedIn results state variable with the response data
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  };

  return (
    <div>
      <h1>Face Detection</h1>

      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleImageUpload} accept="image/*" />
        <button type="submit">Detect Faces</button>
      </form>

      <form onSubmit={handleLinkedInSubmit}> {/* New form for LinkedIn URLs */}
        <textarea onChange={handleLinkedInUrlsChange} value={linkedInUrls} placeholder="Enter LinkedIn URLs, one per line" />
        <button type="submit">Submit LinkedIn URLs</button>
      </form>

      <div className="results">
        {results.length === 0 ? (
          <p>No known faces were detected in the image.</p>
        ) : (
          results.map((result, index) => (
            <div key={index}>
              <p>Name: {result.name}</p>
              <p>About: {result.about}</p>
            </div>
          ))
        )}
      </div>
      <div className="linkedin-results">
        {linkedInResults.map((result, index) => (
          <p key={index}>{result}</p> // Display each LinkedIn result
        ))}
      </div>
    </div>
  );
}

export default App;

