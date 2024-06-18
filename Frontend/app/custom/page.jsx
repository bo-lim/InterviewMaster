'use client';
import axios from "axios"
import DevImg from '../../components/Devlmg';
import Badge from "../../components/Badge";
import { useState } from 'react';
import { useRouter } from 'next/navigation'; // next/navigation에서 useRouter를 가져옴
import { Button } from "../../components/ui/button";
import { Cookies } from 'react-cookie';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { RiBriefcase4Fill, RiTeamFill, RiTodoFill } from "react-icons/ri";

const CustomDialog = () => {
  const user_id = 'ygang4546@gmail.com';
  const [step, setStep] = useState(1);
  const [job, setJob] = useState("");
  const [file, setFile] = useState(null);
  // const [userId, setUserId] = useState(""); // user_id 상태 추가
  // const [textUrl, setTextUrl] = useState(""); // itv_text_url 상태 추가
  const router = useRouter();
  const bucket = process.env.NEXT_PUBLIC_BUCKET_NAME;
  const s3_client = new S3Client({
    region: 'ap-northeast-2',
    credentials: {
      accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY,
    },
  });

  const handleNext = () => {
    setStep(step + 1);
  };
  const file_key = `coverletter/${user_id}_${Date.now()}_`;
  const handleSubmit = async () => {
    const cookies = new Cookies();

    console.log(file);
    const command = new PutObjectCommand({
      Key: file_key+file.name,
      Body: file,
      Bucket: bucket,
    });
    try {
      const response = await s3_client.send(command);
      console.log(response);
    } catch (err) {
      console.error(err);
    }
    // FormData 생성 및 데이터 추가
 
    const response = axios.post(`${process.env.NEXT_PUBLIC_POST_API}/new_itv`, 
      {user_id: user_id,
        itv_text_url: file_key+file.name,
        itv_job: job,
        itv_cate: "자소서"
      })
    .then(function (response) {
      console.log(response);
      cookies.set('itv_no', response.data.new_itv_no);
      cookies.set('coverletter_url', `s3://${bucket}/${file_key}${file.name}`);
      cookies.set('position', job);
    })
    .catch(function (error) {
      console.log(error);
    });
    

    router.push('/information');
  };



  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button className='gap-x-2'>Start !</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          {step === 1 ? (
            <>
              <DialogTitle>관심 직무를 입력해주세요.</DialogTitle>
              <DialogDescription>
                예시: 클라우드 엔지니어
              </DialogDescription>
            </>
          ) : (
            <DialogTitle>자기소개서 파일을 첨부해주세요.</DialogTitle>
          )}
        </DialogHeader>
        {step === 1 ? (
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="job" className="text-right">
                관심 직무
              </Label>
              <Input
                id="job"
                onChange={(e) => setJob(e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
        ) : (
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="file" className="text-right">
                파일 첨부
              </Label>
              <Input
                id="file"
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                className="col-span-3"
              />
            </div>
          </div>
        )}
        <DialogFooter>
          {step === 1 ? (
            <Button onClick={handleNext}>NEXT</Button>
          ) : (
            <Button type="button" onClick={handleSubmit}>SUBMIT</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
const Custom = () => {
  return (
    <section className='py-12 xl:py-24 h-[84vh] xl:pt-28 bg-hero bg-no-repeat bg-bottom bg-cover dark:bg-none'>
      <div className='container mx-auto'>
        <div className='flex justify-between gap-x-8'>
          <div>
            <div className='text-sm uppercase font-semibold mb-4 text-primary tracking-[4px]'>
              Web Service
            </div>
            <h1 className="section-title mb-8 xl:mb-16 text-center mx-auto">
              자소서 기반 면접 Service
            </h1>

            <p className='subtitle max-w-[490px] mx-auto xl:mx-0'>
            "step1. 관심 직무를 적어주세요!"
            
            </p>
            <div>
              <CustomDialog />
            </div>
          </div>
          <div className='hidden xl:flex relative'>
            <Badge 
              containerStyles='absolute top-[24%] -left-[5rem]'
              icon={<RiBriefcase4Fill />}
              endCountNum={3}
              badgeText={'Best Service'}
            />
            <Badge 
              containerStyles='absolute top-[80%] -left-[1rem]'
              icon={<RiTodoFill />}
              endCountNum={6}
              endCountText='k'
              badgeText={'Like Number'}
            />
            <Badge 
              containerStyles='absolute top-[55%] -right-8'
              icon={<RiTeamFill />}
              endCountNum={9}
              endCountText='k'
              badgeText={'Happy Clients'}
            />

            <div className='bg-hero_shape2_dark dark:bg-hero_shape2_light w-[500px] h-[500px] bg-no-repeat absolute -top-1 -right-2 bg-opacity-50'></div>
            <DevImg 
              containerStyles=' w-[700px] h-[450px] bg-no-repeat relative bg-bottom'
              imgSrc='/custom/custom.png'/>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Custom;
