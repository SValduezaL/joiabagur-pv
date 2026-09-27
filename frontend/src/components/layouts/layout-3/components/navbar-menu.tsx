import { ChevronDown } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { MENU_SIDEBAR } from '@/config/layout-3.config';
import { MenuConfig } from '@/config/types';
import { cn } from '@/lib/utils';
import { useMenu } from '@/hooks/use-menu';
import {
  Menubar,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSub,
  MenubarSubContent,
  MenubarSubTrigger,
  MenubarTrigger,
} from '@/components/ui/menubar';

export function NavbarMenu() {
  const { pathname } = useLocation();

  // La cadena original traia cuatro `else if` con la condicion IDENTICA
  // (`pathname.includes('/layout-3')`), asi que las tres ultimas eran inalcanzables: la primera
  // gana siempre. Se colapsa sin cambiar el comportamiento — mismas dos salidas que antes, `[2]` y
  // `[3]`. Las ramas muertas apuntaban a `MENU_SIDEBAR?.[4]`, `MENU_SIDEBAR_CUSTOM?.[0]` y
  // `MENU_SIDEBAR?.[5]`, y no se puede saber qué ruta debía elegir cada una: la plantilla llegó ya
  // asi en el primer commit del repositorio.
  const navbarMenu = pathname.includes('/layout-3')
    ? MENU_SIDEBAR?.[2]
    : MENU_SIDEBAR?.[3];

  const { isActive, hasActiveChild } = useMenu(pathname);

  const buildMenu = (items: MenuConfig) => {
    return items.map((item, index) => {
      if (item.children) {
        return (
          <MenubarMenu key={index}>
            <MenubarTrigger
              className={cn(
                'flex items-center gap-1 px-0 py-3.5 text-sm text-secondary-foreground text-nowrap',
                'rounded-none border-b-2 border-transparent bg-transparent!',
                'hover:text-mono hover:bg-transparent',
                'focus:text-mono focus:bg-transparent',
                'data-[state=open]:bg-transparent data-[state=open]:text-mono',
                'data-[here=true]:text-mono data-[here=true]:border-mono',
              )}
              data-active={isActive(item.path) || undefined}
              data-here={hasActiveChild(item.children) || undefined}
            >
              {item.title}
              <ChevronDown className="ms-auto size-3.5!" />
            </MenubarTrigger>
            <MenubarContent className="min-w-[175px]" sideOffset={0}>
              {buildSubMenu(item.children)}
            </MenubarContent>
          </MenubarMenu>
        );
      } else {
        return (
          <MenubarMenu key={index}>
            <MenubarTrigger
              asChild
              className={cn(
                'flex items-center py-3.5 text-sm text-secondary-foreground px-3 text-nowrap',
                'rounded-none border-b-2 border-transparent bg-transparent!',
                'hover:text-mono hover:bg-transparent',
                'focus:text-mono focus:bg-transparent',
                'data-[active=true]:text-mono data-[active=true]:border-mono',
              )}
            >
              <Link
                to={item.path || ''}
                data-active={isActive(item.path) || undefined}
                data-here={hasActiveChild(item.children) || undefined}
              >
                {item.title}
              </Link>
            </MenubarTrigger>
          </MenubarMenu>
        );
      }
    });
  };

  const buildSubMenu = (items: MenuConfig) => {
    return items.map((item, index) => {
      if (item.children) {
        return (
          <MenubarSub key={index}>
            <MenubarSubTrigger
              data-active={isActive(item.path) || undefined}
              data-here={hasActiveChild(item.children) || undefined}
            >
              <span>{item.title}</span>
            </MenubarSubTrigger>
            <MenubarSubContent className="min-w-[175px]">
              {buildSubMenu(item.children)}
            </MenubarSubContent>
          </MenubarSub>
        );
      } else {
        return (
          <MenubarItem
            key={index}
            asChild
            data-active={isActive(item.path) || undefined}
            data-here={hasActiveChild(item.children) || undefined}
          >
            <Link to={item.path || ''}>{item.title}</Link>
          </MenubarItem>
        );
      }
    });
  };

  return (
    <div className="grid">
      <div className="kt-scrollable-x-auto flex items-stretch">
        <Menubar className="space-x-0 flex items-stretch border-none bg-transparent gap-5 p-0 h-auto">
          {buildMenu(navbarMenu.children as MenuConfig)}
        </Menubar>
      </div>
    </div>
  );
}
