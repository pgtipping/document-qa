import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Convert File to FormData for backend request
    const backendFormData = new FormData();
    backendFormData.append("file", file);

    // Forward the file to our backend using axios
    const response = await axios.post(
      "http://localhost:8000/api/upload",
      backendFormData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        // Note: Progress events won't work in server components,
        // we need to handle progress in the client component
      }
    );

    return NextResponse.json(response.data);
  } catch (error) {
    console.error("Upload error:", error);
    if (axios.isAxiosError(error) && error.response) {
      return NextResponse.json(
        { error: error.response.data },
        { status: error.response.status }
      );
    }
    return NextResponse.json(
      { error: "Failed to upload file" },
      { status: 500 }
    );
  }
}
