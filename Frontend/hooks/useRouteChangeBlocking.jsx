import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';

const useBlockPageNavigation = () => {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [routePath, setRoutePath] = useState('');

  const handleRouteChangeStart = (url) => {
    if (url === router.asPath) return;

    if (!isModalOpen) {
      setRoutePath(url);
      setIsModalOpen(true);

      // 페이지 이동 block
      router.events.emit("routeChangeError");
      throw "routeChange aborted.";
    }
  };

  useEffect(() => {
    router.events.on("routeChangeStart", handleRouteChangeStart);

    return () => {
      router.events.off("routeChangeStart", handleRouteChangeStart);
    };
  }, [router.events, isModalOpen]); // dependency array에 router.events와 isModalOpen 추가

  const confirmNavigation = () => {
    setIsModalOpen(false);
    router.push(routePath);
  };

  const cancelNavigation = () => {
    setIsModalOpen(false);
  };

  return {
    isModalOpen,
    confirmNavigation,
    cancelNavigation,
    routePath,
  };
};

export default useBlockPageNavigation;
