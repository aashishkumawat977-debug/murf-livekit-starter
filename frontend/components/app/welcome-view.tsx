'use client';

import Image from 'next/image';
import { Button } from '@/components/ui/button';
import {
  Mic,
  Sparkles,
  BookOpen,
  GraduationCap,
  ArrowRight,
  CheckCircle2,
  Volume2,
} from 'lucide-react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText = 'Start Learning Session',
  onStartCall,
}: WelcomeViewProps) => {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-background px-6 py-12">
      {/* Background Decorative Gradients */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-gradient-to-b from-primary/20 via-indigo-500/10 to-transparent blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 left-1/2 -z-10 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-gradient-to-t from-emerald-500/10 via-amber-500/5 to-transparent blur-3xl" />

      {/* Brand Header */}
      <div className="relative z-10 mb-6 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10 shadow-md backdrop-blur">
          <BookOpen className="h-6 w-6 text-primary" />
        </div>

        <div>
          <p className="text-base font-bold tracking-widest text-foreground">
            ANISHA AI
          </p>
          <p className="text-[11px] font-medium tracking-wider text-muted-foreground uppercase">
            Learning & Literacy Companion
          </p>
        </div>
      </div>

      {/* Anisha 3D Tutor Avatar */}
      <div className="relative z-10 mb-6 flex items-center justify-center">
        {/* Glow & Pulsing Rings */}
        <div className="absolute inset-0 animate-pulse rounded-full bg-primary/25 blur-2xl" />
        <div className="absolute -inset-4 rounded-full border border-primary/20 animate-ping opacity-20" />
        <div className="absolute -inset-2 rounded-full border border-primary/30" />

        <div className="relative h-44 w-44 overflow-hidden rounded-full border-4 border-background bg-gradient-to-tr from-primary/20 to-indigo-500/20 p-1 shadow-2xl">
          <Image
            src="/anisha_avatar.png"
            alt="Anisha AI Tutor"
            width={176}
            height={176}
            className="h-full w-full rounded-full object-cover transition-transform duration-300 hover:scale-105"
            priority
          />
        </div>
      </div>

      {/* State 1: Ready Badge */}
      <div className="relative z-10 mb-6 flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 text-xs font-semibold text-emerald-600 shadow-sm backdrop-blur dark:text-emerald-400">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
        </span>
        State: Ready — Agent is initialized
      </div>

      {/* Hero Content */}
      <section className="relative z-10 flex max-w-2xl flex-col items-center text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-foreground md:text-5xl">
          Empower Learning with <span className="text-primary">Anisha AI</span>
        </h1>

        <p className="mt-4 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
          Your personal voice-powered literacy companion. Practice reading, expand your vocabulary, refine grammar, and speak with confidence!
        </p>

        {/* Learning Badges */}
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card/60 px-3 py-1 text-xs font-medium text-foreground shadow-xs">
            <BookOpen className="h-3.5 w-3.5 text-primary" />
            Reading Practice
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card/60 px-3 py-1 text-xs font-medium text-foreground shadow-xs">
            <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
            Vocabulary Builder
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card/60 px-3 py-1 text-xs font-medium text-foreground shadow-xs">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            Grammar & Pronunciation ✅
          </span>
        </div>

        {/* Single Primary Start Button for Ready State */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-8 h-13 gap-3 rounded-full bg-primary px-8 text-base font-semibold text-primary-foreground shadow-lg transition-all duration-300 hover:scale-105 hover:bg-primary/90 hover:shadow-primary/25"
        >
          <Mic className="h-5 w-5" />
          {startButtonText || 'Start Learning Session'}
          <ArrowRight className="h-5 w-5" />
        </Button>

        {/* Footer Features */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-xs font-medium text-muted-foreground">
          <div className="flex items-center gap-2">
            <Volume2 className="h-4 w-4 text-primary" />
            Real-time Voice AI
          </div>
          <div className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-indigo-500" />
            Literacy Focused
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            Interactive Feedback
          </div>
        </div>
      </section>
    </div>
  );
};