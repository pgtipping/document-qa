"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, File, X, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/components/ui/use-toast";
import axios, { AxiosProgressEvent } from "axios";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      input: React.DetailedHTMLProps<
        React.InputHTMLAttributes<HTMLInputElement>,
        HTMLInputElement
      >;
      p: React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLParagraphElement>,
        HTMLParagraphElement
      >;
      span: React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLSpanElement>,
        HTMLSpanElement
      >;
      div: React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLDivElement>,
        HTMLDivElement
      >;
    }
  }
}

const IconWrapper = ({
  Icon,
  size,
  className,
}: {
  Icon: LucideIcon;
  size: number;
  className?: string;
}) => <Icon size={size} className={className} />;

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      handleUpload(acceptedFiles[0]);
    }
  }, []);

  const handleUpload = async (fileToUpload: File) => {
    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file", fileToUpload);

    try {
      // Upload directly to backend for proper progress tracking
      const response = await axios.post<{ document_id: string }>(
        "http://localhost:8000/api/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent: AxiosProgressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              console.log("Upload progress:", progress);
              setUploadProgress(progress);
            }
          },
        }
      );

      toast({
        title: "Success",
        description: "File uploaded successfully",
        duration: 3000,
      });

      // Store document ID for later use
      localStorage.setItem("currentDocumentId", response.data.document_id);
    } catch (error) {
      console.error("Upload error:", error);
      toast({
        title: "Error",
        description: "Failed to upload file",
        variant: "destructive",
        duration: 3000,
      });
      setFile(null);
    } finally {
      // Only reset upload state after a delay to show 100% progress
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000); // Increased delay to ensure progress is visible
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: isUploading,
  });

  const removeFile = () => {
    if (!isUploading) {
      setFile(null);
      localStorage.removeItem("currentDocumentId");
    }
  };

  return (
    <div className="w-full space-y-4">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 
          transition-all duration-200 ease-in-out
          ${isUploading ? "opacity-50 cursor-not-allowed" : ""}
          ${
            isDragActive
              ? "border-primary bg-primary/5 scale-[1.02]"
              : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <div
            className={`
              p-4 rounded-full 
              transition-all duration-200
              ${
                isDragActive
                  ? "bg-primary/10 text-primary"
                  : "bg-muted text-muted-foreground"
              }
            `}
          >
            <IconWrapper Icon={Upload} size={32} />
          </div>
          <div className="space-y-2">
            <p className="text-base font-medium">
              {isDragActive ? (
                <span className="text-primary">Drop your file here</span>
              ) : (
                "Drag & drop your file here"
              )}
            </p>
            <p className="text-sm text-muted-foreground">
              or click to browse from your computer
            </p>
          </div>
          <div className="text-xs text-muted-foreground/75">
            Supports PDF, TXT, DOC, and DOCX files up to 10MB
          </div>
        </div>
      </div>

      {file && (
        <div className="flex flex-col space-y-2">
          <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
            <div className="flex items-center space-x-4">
              <div className="p-2 rounded-full bg-primary/10">
                <IconWrapper Icon={File} size={24} className="text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium truncate max-w-[200px]">
                  {file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-destructive"
              onClick={removeFile}
              disabled={isUploading}
            >
              <IconWrapper Icon={X} size={16} />
            </Button>
          </div>

          {isUploading && (
            <div className="space-y-2">
              <Progress value={uploadProgress} className="w-full" />
              <p className="text-xs text-center text-muted-foreground">
                Uploading... {Math.round(uploadProgress)}%
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
