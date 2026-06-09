import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
from core.config import settings

# Initialize Cloudinary configuration
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

class CloudinaryService:
    @staticmethod
    def upload_file(file: UploadFile, folder: str = "task_attachments") -> dict:
        """
        Uploads a file to Cloudinary.
        Returns a dictionary with 'secure_url' and 'public_id'.
        """
        # If credentials aren't set, return mock data for development purposes
        if not settings.CLOUDINARY_CLOUD_NAME:
            return {
                "secure_url": f"https://mock-url.com/{file.filename}",
                "public_id": f"mock_public_id_{file.filename}"
            }

        response = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="auto" # Auto detects if it's an image, video, or raw file (PDFs, docs)
        )
        return {
            "secure_url": response.get("secure_url"),
            "public_id": response.get("public_id")
        }

    @staticmethod
    def delete_file(public_id: str):
        """
        Deletes a file from Cloudinary by its public ID.
        """
        if not settings.CLOUDINARY_CLOUD_NAME or public_id.startswith("mock_public_id"):
            return True

        response = cloudinary.uploader.destroy(public_id)
        return response.get("result") == "ok"
