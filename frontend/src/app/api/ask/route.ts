import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { question, documentId } = body;

    if (!question || !documentId) {
      return NextResponse.json(
        { error: "Question and document ID are required" },
        { status: 400 }
      );
    }

    // Forward the question to our backend
    const response = await fetch("http://localhost:8000/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        document_id: documentId,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Question error:", error);
    return NextResponse.json(
      { error: "Failed to get answer" },
      { status: 500 }
    );
  }
}
