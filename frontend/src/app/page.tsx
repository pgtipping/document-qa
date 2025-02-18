"use client";

import FileUpload from "@/components/FileUpload";
import ChatInterface from "@/components/ChatInterface";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      main: React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement>,
        HTMLElement
      >;
    }
  }
}

export default function Home() {
  return (
    <div className="relative">
      {/* Theme Toggle */}
      <div
        className="ml-[50%] mt-[10px]"
        style={{ marginLeft: "50%", marginTop: "10px" }}
      >
        <ThemeToggle />
      </div>

      <main className="min-h-screen bg-gradient-to-b from-background to-muted/20 pt-24">
        <div className="container mx-auto p-6 space-y-8">
          <Card className="border-0 shadow-lg bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5">
            <CardHeader className="space-y-4 pb-8">
              <CardTitle className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
                Document Q&A
              </CardTitle>
              <CardDescription className="text-xl text-muted-foreground">
                Upload your documents and get instant, intelligent answers to
                your questions using advanced AI
              </CardDescription>
            </CardHeader>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <Card className="lg:col-span-1 border shadow-lg hover:shadow-xl transition-all duration-200 hover:border-primary/20 bg-card">
              <CardHeader className="space-y-4">
                <CardTitle className="text-2xl font-semibold bg-gradient-to-r from-primary/80 to-primary bg-clip-text text-transparent">
                  Upload Document
                </CardTitle>
                <CardDescription className="text-base text-muted-foreground">
                  Upload your PDF or text file to start asking questions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload />
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 h-full border shadow-lg hover:shadow-xl transition-all duration-200 hover:border-primary/20 bg-card">
              <CardHeader className="space-y-4">
                <CardTitle className="text-2xl font-semibold bg-gradient-to-r from-primary/80 to-primary bg-clip-text text-transparent">
                  Chat
                </CardTitle>
                <CardDescription className="text-base text-muted-foreground">
                  Ask questions about your document and get AI-powered answers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ChatInterface />
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
