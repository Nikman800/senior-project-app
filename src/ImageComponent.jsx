import React, { useRef } from 'react';

function ImageComponent() {
  const fileInput = useRef(null);

  const handleUploadClick = event => {
    event.preventDefault();
    fileInput.current.click();
  };

  const handleFileChange = event => {
    const file = event.target.files[0];
    console.log('Selected file', file);
    // Here you can handle the file upload. For example, send it to a server.
  };

  return (
    <div>
      <input
        type="file"
        style={{ display: 'none' }}
        ref={fileInput}
        onChange={handleFileChange}
      />
      <button onClick={handleUploadClick}>Upload Image</button>
      <button onClick={() => { console.log('Identify People in Image button clicked'); }}>Identify People in Image</button>
    </div>
  );
}

export default ImageComponent;