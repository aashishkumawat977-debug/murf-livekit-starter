'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  useAgent,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';

import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';

import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({
  top = false,
  bottom = false,
  className,
}: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,

  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);

  const [chatOpen, setChatOpen] = useState(false);
  const [microphoneError, setMicrophoneError] = useState(false);

  const scrollAreaRef = useRef<HTMLDivElement | null>(null);

  useAgent();

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop =
        scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleDeviceError = ({
    source,
    error,
  }: {
    source: Track.Source;
    error: Error;
  }) => {
    if (source !== Track.Source.Microphone) {
      return;
    }

    const errorName = String(error?.name ?? '').toLowerCase();
    const errorMessage = String(error?.message ?? '').toLowerCase();

    if (
      errorName.includes('notallowed') ||
      errorName.includes('permission') ||
      errorMessage.includes('permission denied') ||
      errorMessage.includes('notallowed') ||
      errorMessage.includes('permission')
    ) {
      setMicrophoneError(true);
    }
  };

  /*
   * IMPORTANT:
   *
   * AgentControlBar is rendered ONLY while the LiveKit
   * session is connected.
   *
   * When the call ends, session.isConnected becomes false.
   * The complete control bar is immediately removed.
   *
   * This prevents the microphone/camera/device dropdown
   * components from remaining on screen after disconnect.
   */
  const isSessionConnected = session.isConnected;

  return (
    <section
      className={cn(
        'bg-background relative z-10 h-full w-full overflow-hidden',
        className
      )}
      {...props}
    >
      {chatOpen && (
  <motion.div
    {...CHAT_MOTION_PROPS}
    className="absolute inset-x-3 top-[115px] bottom-24 z-20 mx-auto flex w-auto max-w-2xl flex-col overflow-hidden rounded-2xl border border-border/50 bg-background/95 shadow-2xl backdrop-blur-md md:inset-x-12 md:top-[115px] md:bottom-32"
  >
    <AgentChatTranscript
      messages={messages}
      className="min-h-0 flex-1 overflow-y-auto"
    />
  </motion.div>
)}
<TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={audioVisualizerColorShift}
        audioVisualizerBarCount={audioVisualizerBarCount}
        audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
        audioVisualizerRadialRadius={audioVisualizerRadialRadius}
        audioVisualizerGridRowCount={audioVisualizerGridRowCount}
        audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
        audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
      />

      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && !microphoneError && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold"
              >
                {preConnectMessage}
              </MotionMessage>
            )}
          </AnimatePresence>
        )}

        <AnimatePresence>
          {microphoneError && isSessionConnected && (
            <motion.div
              initial={{
                opacity: 0,
                y: 15,
                scale: 0.95,
              }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
              }}
              exit={{
                opacity: 0,
                y: 10,
                scale: 0.95,
              }}
              transition={{
                duration: 0.3,
                ease: 'easeOut',
              }}
              className="mx-auto mb-4 w-full max-w-xl"
            >
              <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-center shadow-xl backdrop-blur-lg">
                <div className="flex items-center justify-center gap-2 text-sm font-bold text-destructive">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-destructive/20">
                    
                  </span>

                  Microphone Access Blocked
                </div>

                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                  Anisha AI requires microphone access so you can speak with the agent.
                </p>

                <div className="mt-3 space-y-1.5 rounded-xl border border-border/50 bg-background/60 p-3 text-left text-xs text-foreground">
                  <p className="font-semibold text-destructive/90">
                    How to enable your microphone:
                  </p>

                  <ol className="list-inside list-decimal space-y-1 text-muted-foreground">
                    <li>
                      Click the lock or settings icon next to the address
                      bar URL.
                    </li>

                    <li>
                      Find{' '}
                      <strong className="text-foreground">
                        Microphone
                      </strong>{' '}
                      permissions and select{' '}
                      <strong className="text-emerald-600 dark:text-emerald-400">
                        Allow
                      </strong>
                      .
                    </li>

                    <li>
                      Click the Retry button below or refresh the page.
                    </li>
                  </ol>
                </div>

                <div className="mt-3 flex justify-center gap-2">
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        await navigator.mediaDevices.getUserMedia({
                          audio: true,
                        });

                        setMicrophoneError(false);
                      } catch {
                        setMicrophoneError(true);
                      }
                    }}
                    className="rounded-full bg-destructive px-5 py-1.5 text-xs font-semibold text-destructive-foreground shadow-md transition hover:bg-destructive/90 active:scale-95"
                  >
                    Grant Permission & Retry
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade
            bottom
            className="absolute inset-x-0 top-0 h-4 -translate-y-full"
          />

          {/*
           * THE IMPORTANT FIX:
           *
           * The complete AgentControlBar is removed from the DOM
           * as soon as LiveKit disconnects.
           *
           * This prevents the raw red microphone/camera/device
           * buttons from appearing at the bottom after the call.
           */}
          {isSessionConnected && (
            <AgentControlBar
              key="connected-agent-controls"
              variant="livekit"
              controls={controls}
              isChatOpen={chatOpen}
              isConnected={true}
              onDisconnect={session.end}
              onIsChatOpenChange={setChatOpen}
              onDeviceError={handleDeviceError}
            />
          )}
        </div>
      </motion.div>
    </section>
  );
}



