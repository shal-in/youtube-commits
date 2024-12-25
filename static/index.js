const urlInputEl = document.getElementById("url");
const urlSubmitEl = document.getElementById("url-submit");

urlSubmitEl.addEventListener("click", async () => {
    let youtubeURL = urlInputEl.value;

    const url = "http://127.0.0.1:8000/api/get_channel_info";

    const payload = {
        "url": youtubeURL
    };

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const data = await response.json();

            console.log("Channel info received", data);
            
            let uploads = await getUploads(data);
            
            processUploads(uploads);

        } else {
            console.error("Error:", response.status, await response.text());
            alert(`Error: ${response.status}\n${await response.text()}`);
        }
    } catch (error) {
        console.error("Network Error:", error);
    }
});

async function getUploads(data) {
    let requestURL = "http://127.0.0.1:8000/api/get_uploads";

    payload = {
        "metadata": data
    }
    
    try {
        const response = await fetch(requestURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const data = await response.json();
            console.log("Uploads received:", data["data"]);
            return data["data"]["uploads"]; // Return the data if needed
        } else {
            const errorMessage = await response.text();
            console.error("Error:", response.status, errorMessage);
            alert(`Error: ${response.status}\n${errorMessage}`);
        }
    } catch (error) {
        console.error("Network Error:", error);
    }
}

function processUploads(uploads) {
    const keys = Object.keys(uploads).map(Number);

    const minKey = Math.min(...keys);
    const maxKey = Math.max(...keys);

    for (let year=minKey; year<=maxKey; year++) {
        let numUploads = uploads[year].length

        console.log(`${year}: ${numUploads} videos`);
    }
}