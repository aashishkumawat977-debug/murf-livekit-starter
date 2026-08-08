'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import { Loader2, RefreshCw, Sparkles, BookOpen, Mic } from 'lucide-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { Button } from '@/components/ui/button';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1, scale: 1 },
    hidden: { opacity: 0, scale: 0.98 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.4,
    ease: 'easeInOut',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const { resolvedTheme } = useTheme();

  const isConnected = session.isConnected;
  const isConnecting = session.connectionState === 'connecting';

  // Track if a call was active previously to identify 'Call Ended' state
  const [wasConnected, setWasConnected] = useState(false);
  const [hasEnded, setHasEnded] = useState(false);

  useEffect(() => {
    if (isConnected) {
      setWasConnected(true);
      setHasEnded(false);
    } else if (wasConnected && !isConnecting && !isConnected) {
      setHasEnded(true);
    }
  }, [isConnected, isConnecting, wasConnected]);

  const handleStartAgain = () => {
    setHasEnded(false);
    setWasConnected(false);
    session.start();
  };

  return (
    <AnimatePresence mode="wait">
      {/* State 2: Connecting View */}
      {isConnecting && (
        <motion.div
          key="connecting-state"
          {...VIEW_MOTION_PROPS}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/95 px-6 backdrop-blur-lg"
        >
          <div className="relative mb-6 flex items-center justify-center">
            <div className="absolute inset-0 animate-ping rounded-full bg-primary/20 blur-xl" />
            <div className="relative h-36 w-36 overflow-hidden rounded-full border-4 border-primary/40 p-1 shadow-2xl">
              <Image
                src="/anisha_avatar.png"
                alt="Anisha AI"
                width={144}
                height={144}
                className="h-full w-full rounded-full object-cover"
              />
            </div>
            <div className="absolute -bottom-2 rounded-full border border-primary/30 bg-background px-3 py-1 text-xs font-semibold text-primary shadow-md flex items-center gap-1.5">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Connecting...
            </div>
          </div>

          <div className="text-center max-w-md">
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-4 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 mb-3">
              State: Connecting — Joining call
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Connecting to Anisha AI
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Please wait while we establish a secure real-time voice room and prepare your literacy session...
            </p>
          </div>
        </motion.div>
      )}

      {/* State 5: Call Ended View */}
      {!isConnected && !isConnecting && hasEnded && (
        <motion.div
          key="call-ended-state"
          {...VIEW_MOTION_PROPS}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background px-6"
        >
          {/* Background Decorative Gradients */}
          <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[400px] w-[400px] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />

          <div className="relative mb-6 flex flex-col items-center">
            <div className="relative h-32 w-32 overflow-hidden rounded-full border-4 border-muted p-1 shadow-xl grayscale-20">
              <Image
                src="/anisha_avatar.png"
                alt="Anisha AI"
                width={128}
                height={128}
                className="h-full w-full rounded-full object-cover"
              />
            </div>
            <span className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-zinc-500/30 bg-zinc-500/10 px-4 py-1 text-xs font-semibold text-zinc-600 dark:text-zinc-400">
              State: Call Ended — Conversation Completed
            </span>
          </div>

          <div className="text-center max-w-md">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
              Learning Session Ended
            </h2>
            <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
              Great job practicing today! You can start a new voice session anytime to continue building your reading and vocabulary skills.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button
                size="lg"
                onClick={handleStartAgain}
                className="h-12 gap-2.5 rounded-full bg-primary px-7 text-base font-semibold text-primary-foreground shadow-md transition-transform hover:scale-105"
              >
                <RefreshCw className="h-5 w-5" />
                Start Again
              </Button>
            </div>
          </div>
        </motion.div>
      )}

      {/* State 1: Ready View */}
      {!isConnected && !isConnecting && !hasEnded && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText || 'Start Learning Session'}
          onStartCall={session.start}
        />
      )}

      {/* State 3 & 4: Session View (Listening & Speaking) */}
      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}

