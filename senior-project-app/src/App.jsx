import { useEffect, useState } from "react";
import { BrowserRouter, Link, Switch, Route } from 'react-router-dom';
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
// import axios from "axios";

// import React, { useState } from 'react';

function App() {
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);

  const handleImageUpload = (event) => {
    setImage(event.target.files[0]);
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const formData = new FormData();
    formData.append("image", image);

    fetch("http://localhost:8080/detect_faces", {
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

  return (
    <div>
      <h1>Face Detection</h1>

      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleImageUpload} accept="image/*" />
        <button type="submit">Detect Faces</button>
      </form>

      <div className="results">
        {results &&
          results.map((result, index) => {
            const [imagePath, value] = Object.entries(result)[0];
            return (
              <div key={index}>
                <p>Image: {imagePath}</p>
                {typeof value === "string" ? (
                  <p>Result: {value}</p>
                ) : (
                  Object.entries(value).map(([key, val], i) => (
                    <p key={i}>{`${key}: ${JSON.stringify(val)}`}</p>
                  ))
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}

export default App;

// function App() {
//   const [count, setCount] = useState(0)
//   const [array, setArray] = useState([])

//   const fetchAPI = async () => {
//     const response = await axios.get('http://localhost:8080/api/users');
//     setArray(response.data.users);
//   };

//   useEffect(() => {
//     fetchAPI();
//   }, []);

//   return (
//     <>
//       <div>
//         <a href="https://vitejs.dev" target="_blank">
//           <img src={viteLogo} className="logo" alt="Vite logo" />
//         </a>
//         <a href="https://react.dev" target="_blank">
//           <img src={reactLogo} className="logo react" alt="React logo" />
//         </a>
//       </div>
//       <h1>Vite + React</h1>
//       <div className="card">
//         <button onClick={() => setCount((count) => count + 1)}>
//           count is {count}
//         </button>

//           {array.map((user,index) => (
//             <div key={index}>
//               <span key={index}>{user}</span>
//               <br></br>
//             </div>
//           ))}

//       </div>
//       <p className="read-the-docs">
//         Click on the Vite and React logos to learn more
//       </p>
//     </>
//   )
// }

// export default App
