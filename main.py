import youtube
from datetime import date
from pydantic import BaseModel, RootModel
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

# FastAPI
app = FastAPI()

# Define a Pydantic model to validate the incoming data
class URLRequest(BaseModel):
    url: str

class ChannelRequest(BaseModel):
    metadata: Dict[str, Any]

api_key = youtube.get_api_key()
youtube_service = youtube.get_youtube(api_key)

@app.get("/")
def index():
    return {"message": "Hello from the server!"}

# API
@app.post("/api/get_channel_info")
async def get_channel_info(request: URLRequest):
    url = request.url

    if not url:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "URL is required."})

    try:
        # Call the get_channel_id function from your youtube helper module
        channel_id = youtube.get_channel_id(url)

        channel_info = youtube.get_channel_details(channel_id)

        # If successful, return the channel ID
        return channel_info

    except ValueError as e:
        # Return an error response with appropriate message if URL is invalid
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)})
    except Exception as e:
        # Handle any other unexpected errors
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "An unexpected error occurred."})


# API to handle the POST request with channel data

@app.post("/api/get_uploads")
async def get_uploads(channel_request: ChannelRequest):
    try:
        # Access the metadata dictionary from the request
        data = channel_request.metadata
        
        # Check if the required key exists in the metadata
        if "uploads_playlist_id" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The 'uploads_playlist_id' field is missing from the request data."
            )

        uploads_playlist_id = data["uploads_playlist_id"]

        # Get video IDs using YouTube API function
        try:
            video_ids = youtube.get_video_ids(uploads_playlist_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching video IDs: {str(e)}"
            )

        # Get video details using YouTube API function
        try:
            all_video_info = youtube.get_video_details(video_ids)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching video details: {str(e)}"
            )

        # Preprocess video details
        try:
            all_video_info = youtube.preprocess_video_details(all_video_info)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error preprocessing video details: {str(e)}"
            )

        # Query video data by year
        try:
            all_video_info = youtube.query_data_by_year(all_video_info)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error querying video data by year: {str(e)}"
            )

        # Add the uploads data to the original metadata
        data["uploads"] = all_video_info

        return {"message": "Channel data received", "data": data}

    except HTTPException as http_exc:
        # Handle known HTTP exceptions and return the response
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"message": http_exc.detail}
        )

    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"An unexpected error occurred: {str(e)}"}
        )