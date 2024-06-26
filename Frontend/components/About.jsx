import DevImg from "./Devlmg";
// import Image from "next/image";
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import {User2, MailIcon, HomeIcon, PhoneCall } from  'lucide-react'
import Link from "next/link"
// import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar"
// import { Input } from "./ui/input"
// import { Button } from "/ui/button"


const About = () => {
  return ( 
    <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
      
          <div className="container px-4 md:px-6">
            <div className="grid gap-6 lg:grid-cols-[1fr_400px] lg:gap-12 xl:grid-cols-[1fr_600px]">
              <div className="flex flex-col justify-center space-y-4">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
                    AI 모의 면접으로 취업 준비를 시작하세요.
                  </h1>
                  <p className="max-w-[600px] text-muted-foreground md:text-xl">
                    AI 기반 모의 면접 서비스로 실전 면접 실력을 키워보세요. 전문가 피드백과 함께 면접 스킬을 향상시킬 수
                    있습니다.
                  </p>
                </div>
                <div className="flex flex-col gap-2 min-[400px]:flex-row">
                  <Link
                    href='/login'
                    className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
                    prefetch={false}
                  >
                    모의 면접 시작하기
                  </Link>
                </div>
                
              </div>
              <div className="hidden xl:flex flex-1 relative">
            <DevImg 
              containerStyles='bg-about_shape_dark dark:bg-avout_shape_dark w-[505px] h-[505px] bg-no-repeat relative' 
              imgSrc='/about/about.png' 
            />
          </div>
              {/* <img
                src="/placeholder.svg"
                width="550"
                height="550"
                alt="Hero"
                className="mx-auto aspect-video overflow-hidden rounded-xl object-cover sm:w-full lg:order-last lg:aspect-square"
              /> */}
            </div>
          </div>
        </section>
  
  );
};

export default About;