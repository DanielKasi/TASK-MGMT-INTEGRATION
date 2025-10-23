"use client"

import type React from "react"

import { useState, useRef, useEffect, useCallback } from "react"
import { Send, Smile } from "lucide-react"
import { Button } from "@/platform/v1/components"
import { Textarea } from "@/platform/v1/components"
import { Popover, PopoverContent, PopoverTrigger } from "@/platform/v1/components"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  maxLength?: number
}

const EMOJI_LIST = ["👍", "❤️", "😊", "😂", "🎉", "🔥", "👏", "✨", "💯", "🚀"]
const DEFAULT_MAX_LENGTH = 2000

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Type a message...",
  maxLength = DEFAULT_MAX_LENGTH,
}: ChatInputProps) {
  const [message, setMessage] = useState("")
  const [isFocused, setIsFocused] = useState(false)
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [message])

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled && !isSending) {
      setIsSending(true)
      try {
        await onSend(message.trim())
        setMessage("")
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto"
        }
      } catch (error) {
        console.error("Failed to send message:", error)
      } finally {
        setIsSending(false)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const insertEmoji = useCallback((emoji: string) => {
    setMessage((prev) => prev + emoji)
    setShowEmojiPicker(false)
    textareaRef.current?.focus()
  }, [])

  return (
    <div className="w-full space-y-2 p-2 sm:p-3" role="region" aria-label="Chat input area">
      {/* Input Container */}
      <form onSubmit={handleSubmit} className="w-full">
        <div
          className={cn(
            "flex gap-2 items-end p-2 sm:p-3 bg-white rounded-2xl border-2 transition-all duration-200",
            isFocused
              ? "border-blue-500 shadow-lg ring-4 ring-blue-50"
              : "border-gray-200 hover:border-gray-300 shadow-sm",
            disabled && "opacity-50 cursor-not-allowed bg-gray-50",
          )}
        >
          {/* Emoji Picker */}
          <div className="flex items-center">
            <Popover open={showEmojiPicker} onOpenChange={setShowEmojiPicker}>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  disabled={disabled}
                  className="h-8 w-8 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                  title="Add emoji"
                  aria-label="Open emoji picker"
                >
                  <Smile className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-2" align="start">
                <div className="grid grid-cols-5 gap-1">
                  {EMOJI_LIST.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => insertEmoji(emoji)}
                      className="h-10 w-10 flex items-center justify-center text-2xl hover:bg-gray-100 rounded-lg transition-colors"
                      aria-label={`Insert ${emoji} emoji`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </PopoverContent>
            </Popover>
          </div>

          {/* Textarea */}
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value.slice(0, maxLength))}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              className={cn(
                "min-h-[36px] max-h-[150px] resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0 p-1 text-sm bg-transparent shadow-none",
                message.length > maxLength * 0.9 && "text-orange-500",
              )}
              aria-label="Message input"
            />
          </div>

          {/* Send Button */}
          <Button
            type="submit"
            size="icon"
            disabled={disabled || !message.trim() || isSending}
            className="h-9 w-9 flex-shrink-0 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 disabled:scale-100"
            aria-label="Send message"
          >
            {isSending ? (
              <svg
                className="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Helper Text */}
        <div className="flex items-center justify-between px-2 mt-1.5">
          <p className="text-xs text-gray-400">
            <span className="hidden sm:inline">Press Enter to send, Shift + Enter for new line</span>
            <span className="sm:hidden">Enter to send</span>
          </p>
          <p className={cn("text-xs", message.length > maxLength * 0.9 ? "text-orange-500" : "text-gray-400")}>
            {message.length}/{maxLength}
          </p>
        </div>
      </form>
    </div>
  )
}
