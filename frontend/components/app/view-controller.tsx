'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();

  const [isConnecting, setIsConnecting] = useState(false);
  const [showGoodbye, setShowGoodbye] = useState(false);

  const wasConnected = useRef(false);

  useEffect(() => {
    if (isConnected) {
      wasConnected.current = true;
      setIsConnecting(false);
      setShowGoodbye(false);
      return;
    }

    if (wasConnected.current) {
      wasConnected.current = false;
      setShowGoodbye(true);

      const timer = window.setTimeout(() => {
        setShowGoodbye(false);
      }, 2500);

      return () => window.clearTimeout(timer);
    }
  }, [isConnected]);

  const handleStartCall = async () => {
    setShowGoodbye(false);
    setIsConnecting(true);

    try {
      await start();
    } catch (error) {
      setIsConnecting(false);
      throw error;
    }
  };

  return (
    <AnimatePresence mode="wait">
      {/* Goodbye view after call ends */}
      {showGoodbye && !isConnected && (
        <motion.div
          key="goodbye"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 1.02 }}
          transition={{
            duration: 0.5,
            ease: 'easeInOut',
          }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background"
        >
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.6,
              ease: 'easeOut',
            }}
            className="flex flex-col items-center text-center px-6"
          >
            <div className="mb-6 h-28 w-28 overflow-hidden rounded-full border-4 border-background shadow-2xl">
              <img
                src="/anisha_avatar.png"
                alt="Anisha AI"
                className="h-full w-full object-cover"
              />
            </div>

            <h2 className="text-2xl font-bold text-foreground">
              Thanks for learning with Anisha!
            </h2>

            <p className="mt-2 text-center text-sm text-muted-foreground">
              Your learning session has ended.
            </p>
          </motion.div>
        </motion.div>
      )}

      {/* Welcome view */}
      {!isConnected && !isConnecting && !showGoodbye && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStartCall}
        />
      )}

      {/* Connecting view */}
      {isConnecting && !isConnected && !showGoodbye && (
        <motion.div
          key="connecting"
          {...VIEW_MOTION_PROPS}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background"
        >
          <div className="mb-6 h-32 w-32 overflow-hidden rounded-full border-4 border-background shadow-2xl">
            <img
              src="/anisha_avatar.png"
              alt="Anisha AI"
              className="h-full w-full object-cover"
            />
          </div>

          <h2 className="text-2xl font-bold text-foreground">
            Connecting to Anisha AI…
          </h2>

          <p className="mt-2 text-center text-sm text-muted-foreground">
            Please wait while we connect you to your learning assistant.
          </p>
        </motion.div>
      )}

      {/* Session view */}
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
          audioVisualizerGridColumnCount={
            appConfig.audioVisualizerGridColumnCount
          }
          audioVisualizerRadialBarCount={
            appConfig.audioVisualizerRadialBarCount
          }
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}